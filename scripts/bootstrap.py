"""Install pinned official archives locally. No system PATH/policy changes."""
import argparse,hashlib,json,os,platform,stat,subprocess,tarfile,tempfile,urllib.request,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def file_digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def download_verified(url,digest,destination):
    """Commit a cache entry only after a complete, checksum-verified download."""
    if destination.exists() and file_digest(destination)==digest:
        return destination
    destination.parent.mkdir(parents=True,exist_ok=True)
    descriptor,name=tempfile.mkstemp(prefix=destination.name+'-',suffix='.part',dir=destination.parent)
    os.close(descriptor)
    partial=Path(name)
    try:
        urllib.request.urlretrieve(url,partial)
        if file_digest(partial)!=digest:
            raise RuntimeError('checksum mismatch: '+destination.name)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)
    return destination

def make_executable(target):
    """Match the official Unix installer: bin/* plus bin/internal/tcc."""
    candidates=list((target/'bin').iterdir())+[target/'bin/internal/tcc']
    for p in candidates:
        if p.is_file():
            p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def extract(archive,destination):
    destination.mkdir(parents=True,exist_ok=True)
    base=destination.resolve()
    if archive.suffix=='.zip':
        with zipfile.ZipFile(archive) as z:
            for n in z.namelist():
                if not (base/n).resolve().is_relative_to(base):raise ValueError('unsafe archive path')
            z.extractall(base)
    else:
        with tarfile.open(archive) as t:
            for member in t.getmembers():
                p=(base/member.name).resolve()
                if not p.is_relative_to(base):raise ValueError('unsafe archive path')
                if member.issym() and not (p.parent/member.linkname).resolve().is_relative_to(base):raise ValueError('unsafe archive symlink')
                if member.islnk() and not (base/member.linkname).resolve().is_relative_to(base):raise ValueError('unsafe archive hardlink')
            t.extractall(base)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dest',type=Path,default=ROOT/'.tooling/moon');ap.add_argument('--cache',type=Path);a=ap.parse_args()
    cfg=json.loads((ROOT/'toolchain.json').read_text())
    key=('windows' if os.name=='nt' else 'linux')+'_x86_64'
    if platform.machine().lower() not in ('amd64','x86_64'):raise RuntimeError('bootstrap currently supports x86_64 Windows/Linux')
    if os.name!='nt' and platform.system()!='Linux':raise RuntimeError('unsupported bootstrap platform')
    target=a.dest.resolve();exe=target/'bin'/('moon.exe' if os.name=='nt' else 'moon')
    env=dict(os.environ,MOON_HOME=str(target))
    if exe.exists():
        if os.name!='nt':make_executable(target)
        v=subprocess.check_output([exe,'version','--all'],env=env).decode()
        if cfg['compiler_version'] not in v:raise RuntimeError('destination has a different compiler; choose a new directory')
        if not (target/'lib/core/_build/native/release/bundle/prelude/prelude.mi').exists():
            subprocess.run([exe,'bundle','--warn-list','-a','--all'],cwd=target/'lib/core',env=env,check=True)
        if not (target/'registry/index').exists():
            subprocess.run([exe,'update'],cwd=ROOT,env=env,check=True)
        print(str(target));return
    if target.exists() and any(target.iterdir()):raise RuntimeError('refusing to overwrite nonempty destination')
    cache=ROOT/'.tooling/downloads';cache.mkdir(parents=True,exist_ok=True)
    release=cfg['compiler_release'].replace('+','%2B');p=cfg[key]
    sources=[('compiler',f'https://cli.moonbitlang.com/binaries/{release}/{p["archive"]}',p['sha256'],target),
             ('core',f'https://cli.moonbitlang.com/cores/{p["core_archive"]}',p['core_sha256'],target/'lib')]
    for label,url,digest,dest in sources:
        name=url.rsplit('/',1)[1];f=cache/name
        if a.cache:
            candidate=a.cache/('moonbit.zip' if label=='compiler' else 'core-fixed.zip') if os.name=='nt' else a.cache/name
            if candidate.exists():f=candidate
        if f==cache/name:
            f=download_verified(url,digest,f)
        elif file_digest(f)!=digest:
            raise RuntimeError('checksum mismatch in supplied cache: '+name)
        extract(f,dest)
    if os.name!='nt':make_executable(target)
    subprocess.run([exe,'bundle','--warn-list','-a','--all'],cwd=target/'lib/core',env=env,check=True)
    subprocess.run([exe,'update'],cwd=ROOT,env=env,check=True)
    print(subprocess.check_output([exe,'version','--all'],env=env).decode())
    print('MOON_HOME='+str(target))

if __name__=='__main__':main()
