#!/usr/bin/env python3
"""Offline editor for the DACAI panel file system (the 1 MB FAT12 volume "3:/").

Works on a full 2 MB SPI flash backup (made with fel_backup.sh) or on a 1 MB
file-system image. Nothing here talks to the panel; write the result back with
fel_write_fs.sh.

    dacai_fs.py list    BACKUP_OR_IMAGE
    dacai_fs.py extract BACKUP_OR_IMAGE /ICON/2.zico out.zico
    dacai_fs.py delete  BACKUP_OR_IMAGE OUT_IMAGE /MAIN.LUA /IMAGE/22.JPG ...
    dacai_fs.py replace BACKUP_OR_IMAGE OUT_IMAGE /ICON/2.zico new.zico

Paths are case-insensitive and start with "/". delete/replace write a 1 MB
file-system image and verify that every other file is byte-identical.
Only existing files can be replaced; new files and directories are not created.
"""
import argparse
import hashlib
import struct
import sys


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
        return [c for c in range(2, self.clusters + 2) if self.get(c) == 0]

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


def cmd_extract(args):
    fs = load(args.input)
    name, (_e, _l, c, size) = fs.lookup(args.path)
    open(args.output, 'wb').write(fs.read(c, size))
    print(f'{name}: {size} bytes -> {args.output}')


def finish(fs, before, changed, output):
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
    p = sub.add_parser('replace'); p.add_argument('input'); p.add_argument('output'); p.add_argument('path')
    p.add_argument('file'); p.set_defaults(run=cmd_replace)
    args = parser.parse_args(argv)
    args.run(args)


if __name__ == '__main__':
    sys.exit(main())
