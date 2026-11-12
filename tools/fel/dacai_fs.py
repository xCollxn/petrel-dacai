#!/usr/bin/env python3
"""Offline editor for the DACAI panel file system (the 1 MB FAT12 volume "3:/").

Works on a full 2 MB SPI flash backup (made with fel_backup.sh) or on a 1 MB
file-system image. Nothing here talks to the panel; write the result back with
fel_write_fs.sh.

    dacai_fs.py list    BACKUP_OR_IMAGE
    dacai_fs.py extract BACKUP_OR_IMAGE /ICON/2.zico out.zico
    dacai_fs.py delete  BACKUP_OR_IMAGE OUT_IMAGE /MAIN.LUA /IMAGE/22.JPG ...
    dacai_fs.py replace BACKUP_OR_IMAGE OUT_IMAGE /ICON/2.zico new.zico
    dacai_fs.py repair  BACKUP_OR_IMAGE OUT_IMAGE

Paths are case-insensitive and start with "/". delete/replace/repair write a
1 MB file-system image and verify that every other file is byte-identical.
All of them also refresh the panel firmware's own FAT copy when one is present
(see BACKUP_MAGIC); without that the panel restores its old FAT and the edit is
undone. repair
frees clusters that no file owns - left behind when the panel restored an old
FAT after an edit by an older version of this tool.
Only existing files can be replaced; new files and directories are not created.
"""
import argparse
import hashlib
import struct
import sys

# The panel firmware can keep a copy of the boot sector and the FAT in the last
# 16 sectors of the volume, which the FAT itself shows as free: boot sector, FAT,
# then a header sector starting with BACKUP_MAGIC + CRC-16/MODBUS (little endian)
# over boot sector + FAT. When the header is valid and the copy differs from the
# FAT, the firmware restores the FAT from the copy - so an offline edit that
# leaves an old copy behind is undone by the panel (freed clusters come back as
# used but unowned, and the file system fills up). Every write here refreshes a
# copy that is present. The copy is not always there: the firmware also stores
# files in these "free" sectors when space runs short, which overwrites it.
BACKUP_SECTORS = 16
BACKUP_MAGIC = b'\x00\x01\xff\xfe'


def crc16_modbus(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


class Fat12:
    def __init__(self, data):
        self.d = bytearray(data)
        self.base = self._find_boot()
        bps, spc, rsv, nfats, nroot, tot16, _media, spf = struct.unpack_from('<HBHBHHBH', self.d, self.base + 11)
        if bps != 512 or spc != 1 or not tot16 or not spf:
            raise SystemExit('unexpected FAT geometry (expected 512-byte sectors, 1 sector/cluster)')
        self.bps, self.rsv, self.nfats, self.spf, self.total = bps, rsv, nfats, spf, tot16
        self.root_secs = (nroot * 32 + bps - 1) // bps
        self.first_data = rsv + nfats * spf + self.root_secs
        self.clusters = tot16 - self.first_data
        if self.clusters >= 4085:
            raise SystemExit('not a FAT12 volume')
        self.size = tot16 * bps
        self.fats = [self.base + (rsv + i * spf) * bps for i in range(nfats)]
        # Firmware copy of boot sector + FAT in the last 16 sectors (see BACKUP_MAGIC).
        self.backup = tot16 - BACKUP_SECTORS
        self.backup_len = rsv + nfats * spf
        self.backup_header = self.backup + self.backup_len
        if self.backup_header >= tot16:
            raise SystemExit('unexpected FAT geometry (no room for the firmware FAT copy)')
        self.reserved = set(range(max(2, self.backup - self.first_data + 2), self.clusters + 2))

    def _find_boot(self):
        for off in range(0, len(self.d) - 511, 512):
            s = self.d[off:off + 512]
            if s[510:512] == b'\x55\xaa' and s[0x36:0x39] == b'FAT':
                return off
        raise SystemExit('no FAT boot sector found')

    def get(self, c):
        v, = struct.unpack_from('<H', self.d, self.fats[0] + c + c // 2)
        return v >> 4 if c & 1 else v & 0xFFF

    def put(self, c, value):
        for fat in self.fats:
            o = fat + c + c // 2
            v, = struct.unpack_from('<H', self.d, o)
            v = (v & 0x000F) | (value << 4) if c & 1 else (v & 0xF000) | value
            struct.pack_into('<H', self.d, o, v)

    def chain(self, c):
        out = []
        while 2 <= c < 0xFF8 and len(out) <= self.clusters:
            out.append(c)
            c = self.get(c)
        return out

    def coff(self, c):
        return self.base + (self.first_data + c - 2) * self.bps

    def free_clusters(self):
        """Free clusters that are safe to use (never the firmware FAT copy area)."""
        return [c for c in range(2, self.clusters + 2) if self.get(c) == 0 and c not in self.reserved]

    def sector(self, s, n=1):
        return bytes(self.d[self.base + s * self.bps:self.base + (s + n) * self.bps])

    def backup_status(self):
        """'none', 'invalid' (bad CRC), 'stale' (differs from the FAT) or 'current'."""
        header = self.sector(self.backup_header)
        if header[:4] != BACKUP_MAGIC:
            return 'none'
        copy = self.sector(self.backup, self.backup_len)
        if crc16_modbus(copy) != int.from_bytes(header[4:6], 'little'):
            return 'invalid'
        return 'current' if copy == self.sector(0, self.backup_len) else 'stale'

    def sync_backup(self):
        """Bring the firmware FAT copy in line with the FAT: 'none', 'refreshed' or 'invalidated'.

        A copy whose sectors hold file data (the firmware stored a file there)
        is not rewritten, which would damage the file; its header is cleared
        instead, so the firmware has no old FAT to restore.
        """
        if self.backup_status() == 'none':
            return 'none'
        header = self.base + self.backup_header * self.bps
        in_files = {self.first_data + c - 2 for c in self.reachable()}
        if self.backup_header in in_files:
            return 'left'  # the header is file data now; changing it would damage the file
        if in_files & set(range(self.backup, self.backup_header)):
            self.d[header:header + len(BACKUP_MAGIC)] = b'\xff' * len(BACKUP_MAGIC)
            return 'invalidated'
        copy = self.sector(0, self.backup_len)
        start = self.base + self.backup * self.bps
        self.d[start:start + len(copy)] = copy
        self.d[header:header + 6] = BACKUP_MAGIC + crc16_modbus(copy).to_bytes(2, 'little')
        return 'refreshed'

    def reachable(self):
        """Clusters used by files and directories."""
        out = set()
        for clus in self.directories().values():
            if clus:
                out.update(self.chain(clus))
        for _e, _l, c, _size in self.files().values():
            if c:
                out.update(self.chain(c))
        return out

    def orphans(self):
        """Clusters marked used that no file or directory owns (bad clusters excluded)."""
        used = {c for c in range(2, self.clusters + 2) if self.get(c) not in (0, 0xFF7)}
        return sorted(used - self.reachable() - self.reserved)

    def problems(self):
        """Files whose cluster chain does not match their size."""
        out = []
        for name, (_e, _l, c, size) in sorted(self.files().items()):
            chain = self.chain(c) if c else []
            if len(chain) != -(-size // self.bps):
                out.append(f'{name}: {size} bytes but {len(chain)} clusters')
        return out

    def in_backup_area(self):
        """Files the firmware stored in the sectors of its FAT copy (normal when space ran short)."""
        return [name for name, (_e, _l, c, _size) in sorted(self.files().items())
                if c and self.reserved & set(self.chain(c))]

    def _regions(self, clus):
        if clus == 0:
            off = self.base + (self.rsv + self.nfats * self.spf) * self.bps
            return [(off, self.root_secs * self.bps)]
        return [(self.coff(c), self.bps) for c in self.chain(clus)]

    def entries(self, clus):
        """(entry offset, [LFN entry offsets], name, attr, first cluster, size)."""
        lfn, lfn_offs = '', []
        for off, size in self._regions(clus):
            for e in range(off, off + size, 32):
                first = self.d[e]
                if first == 0:
                    return
                if first == 0xE5:
                    lfn, lfn_offs = '', []
                    continue
                if self.d[e + 11] == 0x0F:
                    part = bytes(self.d[e + 1:e + 11] + self.d[e + 14:e + 26] + self.d[e + 28:e + 32])
                    lfn = part.decode('utf-16le', 'ignore').split('\x00')[0] + lfn
                    lfn_offs.append(e)
                    continue
                name = self.d[e:e + 8].decode('latin1').rstrip()
                ext = self.d[e + 8:e + 11].decode('latin1').rstrip()
                hi, = struct.unpack_from('<H', self.d, e + 20)
                lo, = struct.unpack_from('<H', self.d, e + 26)
                size_, = struct.unpack_from('<I', self.d, e + 28)
                yield e, lfn_offs, lfn or name + ('.' + ext if ext else ''), self.d[e + 11], (hi << 16) | lo, size_
                lfn, lfn_offs = '', []

    def directories(self):
        """{'/dir': first cluster} for the root (cluster 0) and every subdirectory."""
        out = {'/': 0}

        def walk(clus, path):
            for _e, _l, name, attr, c, _size in self.entries(clus):
                if name not in ('.', '..') and attr & 0x10 and not attr & 0x08:
                    out[path + '/' + name] = c
                    walk(c, path + '/' + name)
        walk(0, '')
        return out

    def slots(self, clus):
        """Offsets of all 32-byte entry slots of a directory, in order."""
        return [e for off, size in self._regions(clus) for e in range(off, off + size, 32)]

    def usage(self, clus):
        """(live entries, deleted entries, capacity) of a directory."""
        live = deleted = 0
        for e in self.slots(clus):
            if self.d[e] == 0:
                break
            if self.d[e] == 0xE5:
                deleted += 1
            else:
                live += 1
        return live, deleted, len(self.slots(clus))

    def read(self, clus, size):
        return b''.join(bytes(self.d[self.coff(c):self.coff(c) + self.bps]) for c in self.chain(clus))[:size]

    def files(self):
        """{'/dir/name': (entry offset, lfn offsets, first cluster, size)} for every file."""
        out = {}

        def walk(clus, path):
            for e, lfns, name, attr, c, size in self.entries(clus):
                if name in ('.', '..') or attr & 0x08:
                    continue
                if attr & 0x10:
                    walk(c, path + '/' + name)
                else:
                    out[path + '/' + name] = (e, lfns, c, size)
        walk(0, '')
        return out

    def lookup(self, path):
        wanted = '/' + path.strip('/').lower()
        for name, value in self.files().items():
            if name.lower() == wanted:
                return name, value
        raise SystemExit('file not found: ' + path)

    def digests(self):
        return {name: hashlib.sha256(self.read(c, size)).hexdigest()
                for name, (_e, _l, c, size) in self.files().items()}

    def image(self):
        return bytes(self.d[self.base:self.base + self.size])


def load(path):
    return Fat12(open(path, 'rb').read())


def cmd_list(args):
    fs = load(args.input)
    print(f'FAT12 at offset {fs.base:#x}, {fs.size // 1024} KB, {fs.clusters} clusters of {fs.bps} bytes')
    for name, (_e, _l, c, size) in sorted(fs.files().items(), key=lambda item: item[0].lower()):
        print(f'  {name:32s} {size:8d}')
    print(f'free: {len(fs.free_clusters()) * fs.bps // 1024} KB')
    for path, clus in sorted(fs.directories().items()):
        live, deleted, capacity = fs.usage(clus)
        print(f'directory {path}: {live} entries, {deleted} deleted, '
              f'{capacity - live - deleted} never used, {capacity} slots')
    status = fs.backup_status()
    print(f'firmware FAT copy: {status}')
    healthy = True
    if status in ('stale', 'invalid'):
        healthy = False
        print('WARNING: the panel firmware will restore its own (old) FAT copy - an earlier offline '
              'edit did not update it. Run "dacai_fs.py repair" and write the result back.')
    orphans = fs.orphans()
    if orphans:
        healthy = False
        print(f'WARNING: {len(orphans) * fs.bps // 1024} KB used by no file '
              f'(lost space); "dacai_fs.py repair" frees it.')
    for problem in fs.problems():
        healthy = False
        print('WARNING: ' + problem)
    for name in fs.in_backup_area():
        print(f'note: {name} lies in the sectors of the firmware FAT copy (the panel was nearly full)')
    if healthy:
        print('file system consistent')


def cmd_extract(args):
    fs = load(args.input)
    name, (_e, _l, c, size) = fs.lookup(args.path)
    open(args.output, 'wb').write(fs.read(c, size))
    print(f'{name}: {size} bytes -> {args.output}')


def finish(fs, before, changed, output):
    result = fs.sync_backup()
    if result == 'refreshed':
        assert fs.backup_status() == 'current'
        print('firmware FAT copy refreshed')
    elif result == 'invalidated':
        assert fs.backup_status() == 'none'
        print('firmware FAT copy overlaps file data - cleared its header so the panel keeps this FAT')
    elif result == 'left':
        names = ', '.join(fs.in_backup_area())
        raise SystemExit(f'nothing written: the firmware wrote its FAT copy into {names}, so that file '
                         f'is damaged and the panel would restore its old FAT. Delete it first '
                         f'(dacai_fs.py delete), then run repair on the result; Petrel uploads '
                         f'missing pictures again.')
    else:
        print('no firmware FAT copy present - nothing to refresh')
    after = fs.digests()
    for name, digest in after.items():
        if name not in changed and before.get(name) != digest:
            raise SystemExit('verification failed, other file changed: ' + name)
    image = fs.image()
    open(output, 'wb').write(image)
    print(f'free: {len(fs.free_clusters()) * fs.bps // 1024} KB; other files unchanged')
    print(f'wrote {output} ({len(image)} bytes, belongs at flash offset 0x100000), '
          f'sha256 {hashlib.sha256(image).hexdigest()}')


def cmd_delete(args):
    fs = load(args.input)
    before = fs.digests()
    changed = set()
    for path in args.paths:
        name, (e, lfns, c, size) = fs.lookup(path)
        for cluster in fs.chain(c):
            fs.put(cluster, 0)
        for offset in lfns + [e]:
            fs.d[offset] = 0xE5
        changed.add(name)
        print(f'deleted {name} ({size} bytes)')
    finish(fs, before, changed, args.output)


def cmd_repair(args):
    fs = load(args.input)
    before = fs.digests()
    orphans = fs.orphans()
    for cluster in orphans:
        fs.put(cluster, 0)
    print(f'freed {len(orphans) * fs.bps // 1024} KB used by no file')
    for problem in fs.problems():
        print('still to fix (delete or replace the file): ' + problem)
    finish(fs, before, set(), args.output)


def cmd_replace(args):
    fs = load(args.input)
    new = open(args.file, 'rb').read()
    before = fs.digests()
    name, (e, _lfns, first, size) = fs.lookup(args.path)
    old = fs.chain(first)
    need = max(1, -(-len(new) // fs.bps))
    free = fs.free_clusters()
    if need > len(old) + len(free):
        raise SystemExit(f'not enough space: need {need} clusters, have {len(old) + len(free)}')
    use = old[:need] + free[:max(0, need - len(old))]
    for cluster in old[need:]:
        fs.put(cluster, 0)
    for a, b in zip(use, use[1:]):
        fs.put(a, b)
    fs.put(use[-1], 0xFFF)
    for i, cluster in enumerate(use):
        chunk = new[i * fs.bps:(i + 1) * fs.bps]
        fs.d[fs.coff(cluster):fs.coff(cluster) + fs.bps] = chunk + bytes(fs.bps - len(chunk))
    struct.pack_into('<H', fs.d, e + 20, use[0] >> 16)
    struct.pack_into('<H', fs.d, e + 26, use[0] & 0xFFFF)
    struct.pack_into('<I', fs.d, e + 28, len(new))
    if fs.digests()[name] != hashlib.sha256(new).hexdigest():
        raise SystemExit('verification failed: new file does not read back')
    print(f'replaced {name}: {size} -> {len(new)} bytes')
    finish(fs, before, {name}, args.output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('list'); p.add_argument('input'); p.set_defaults(run=cmd_list)
    p = sub.add_parser('extract'); p.add_argument('input'); p.add_argument('path'); p.add_argument('output')
    p.set_defaults(run=cmd_extract)
    p = sub.add_parser('delete'); p.add_argument('input'); p.add_argument('output'); p.add_argument('paths', nargs='+')
    p.set_defaults(run=cmd_delete)
    p = sub.add_parser('repair'); p.add_argument('input'); p.add_argument('output')
    p.set_defaults(run=cmd_repair)
    p = sub.add_parser('replace'); p.add_argument('input'); p.add_argument('output'); p.add_argument('path')
    p.add_argument('file'); p.set_defaults(run=cmd_replace)
    args = parser.parse_args(argv)
    args.run(args)


if __name__ == '__main__':
    sys.exit(main())
