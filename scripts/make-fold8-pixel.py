#!/usr/bin/env python3
"""Build Fold8 Pixel payloads from a pinned base and the exact Pixel SystemUI donor.
No OEM binaries are committed. --review-pins explicitly accepts newly rebuilt hashes.
"""
import argparse,hashlib,os,pathlib,shutil,subprocess,tempfile
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def lines(p):return dict((n,h) for h,n in (s.split() for s in p.read_text().splitlines() if s and not s.startswith('#')))
def run(*a):subprocess.run([str(v) for v in a],check=True)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--base',type=pathlib.Path,required=True)
 p.add_argument('--systemui',type=pathlib.Path,required=True)
 p.add_argument('--relay',type=pathlib.Path,required=True)
 p.add_argument('--out',type=pathlib.Path,required=True)
 p.add_argument('--sdk',type=pathlib.Path,default=pathlib.Path(os.environ.get('ANDROID_HOME','/opt/android-sdk')))
 p.add_argument('--platform',default='android-37.0');p.add_argument('--build-tools',default='36.1.0')
 p.add_argument('--keystore',type=pathlib.Path,default=pathlib.Path.home()/'.android/debug.keystore')
 p.add_argument('--review-pins',action='store_true')
 a=p.parse_args();bt=a.sdk/'build-tools'/a.build_tools;jar=a.sdk/'platforms'/a.platform/'android.jar'
 if a.out.exists():p.error('Output already exists')
 if sha(a.systemui)!='9934d2dac326f56290f459b9e649185cd5531e1b6ae1f5a72b11e88f865f8b03':p.error('Different Pixel donor')
 if sha(a.relay)!='ccf2fbddc462eca6d7cb7f112ca1b36620fe0ccd044ff6ba28bebe13cfe6b89e':p.error('Different OneOS relay')
 a.out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='.pixel-fold8-',dir=a.out.parent) as tmp:
  w=pathlib.Path(tmp);out=w/'set';out.mkdir()
  for n,h in lines(R/'app-android/packages/pixel-f8u.sha256').items():
   f=a.base/n
   if sha(f)!=h:p.error('Base payload differs: '+n)
   shutil.copyfile(f,out/n)
  run('python3',R/'switcher/patches/fold8-pixel/build-systemui.py',a.systemui,'--zipalign',bt/'zipalign','--output',out/'Fold8PixelSystemUI.apk')
  shutil.copyfile(a.relay,out/'Fold8AngleRelay.dex')
  overlay=R/'switcher/overlays/pixel_fold8_unfold'
  run(bt/'aapt2','compile','--dir',overlay/'res','-o',w/'resources.zip')
  run(bt/'aapt2','link','-o',w/'unsigned.apk','--manifest',overlay/'AndroidManifest.xml','-I',jar,'--min-sdk-version','31','--target-sdk-version','36','--auto-add-overlay',w/'resources.zip')
  run(bt/'zipalign','-f','4',w/'unsigned.apk',w/'aligned.apk')
  run(bt/'apksigner','sign','--v4-signing-enabled','false','--ks',a.keystore,'--ks-key-alias','androiddebugkey','--ks-pass','pass:android','--key-pass','pass:android','--out',out/'Fold8PixelUnfold.apk',w/'aligned.apk')
  have={f.name:sha(f) for f in out.iterdir()};pinfile=R/'app-android/packages/pixel-f8.sha256'
  if have!=lines(pinfile):
   if not a.review_pins:p.error('Rebuilt hashes differ (toolchain/ZIP timestamps): review, then use --review-pins to update explicitly')
   text=''.join(h+'  '+n+'\n' for n,h in sorted(have.items()))
   pinfile.write_text(text)
   (R/'app-android/core/model/src/test/resources/packages/pixel-f8.sha256').write_text(text)
  run('python3',R/'scripts/check-dex.py',out/'Fold8PixelSystemUI.apk')
  out.rename(a.out)
 print('Built and verified',a.out)
if __name__=='__main__':main()
