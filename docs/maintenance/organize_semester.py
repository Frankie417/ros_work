from pathlib import Path
import os,csv,json,hashlib,collections,subprocess
ROOT=Path(__file__).resolve().parents[2]
AUDIT=ROOT/'docs'/'maintenance'
AUDIT.mkdir(parents=True,exist_ok=True)
def inventory():
    rows=[];groups=collections.defaultdict(list)
    for base,dirs,files in os.walk(ROOT):
        dirs[:]=sorted(d for d in dirs if d!='.git')
        for name in sorted(files):
            p=Path(base)/name;rel=p.relative_to(ROOT).as_posix()
            if rel.startswith('docs/maintenance/'):continue
            try:
                data=p.read_bytes();sha=hashlib.sha256(data).hexdigest()
            except OSError:continue
            kind=p.suffix.lower();purpose='reference or experiment artifact'
            if kind=='.py':purpose='Python source'
            elif kind=='.ipynb':purpose='Notebook source and saved outputs'
            elif kind in ['.xacro','.urdf','.launch']:purpose='ROS model or launch'
            elif kind in ['.docx','.pdf']:purpose='report or course reference'
            elif kind in ['.csv','.jsonl']:purpose='configuration or experimental records'
            elif kind in ['.png','.jpg','.jpeg','.mp4']:purpose='image or video evidence; inspect context before classifying'
            module='shared/archive'
            low=rel.lower()
            if any(s in low for s in ['arm2026_ws','01_robot_modeling','week1']):module='modeling/platform'
            if any(s in low for s in ['02_robot_arm','week3','week4']):module='motion'
            if any(s in low for s in ['03_visual','week5','week6','visual_grasping']):module='vision'
            if any(s in low for s in ['04_gesture','gesture_usb','week7']):module='gesture (mixed week7 archive)'
            if 'sdk' in low or low.startswith('arm5dof_'):module='vendor SDK/reference'
            rows.append([rel,len(data),sha,module,purpose]);groups[sha].append(rel)
    with (AUDIT/'inventory_before.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['original_path','bytes','sha256','module_hint','purpose']);w.writerows(rows)
    with (AUDIT/'identical_files.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['sha256','path']);w.writerows((h,p) for h,ps in groups.items() if len(ps)>1 for p in ps)
    (AUDIT/'tree_before.txt').write_text('\n'.join(r[0] for r in rows)+'\n',encoding='utf8')
    print(json.dumps({'files':len(rows),'identical_groups':sum(len(v)>1 for v in groups.values()),'agents':[r[0] for r in rows if r[0].endswith('AGENTS.md')]}))
def organize():
    moves=[]
    def move(p,target):
        if not p.exists():return
        assert p.resolve().is_relative_to(ROOT) and target.resolve().is_relative_to(ROOT)
        assert not target.exists(),target
        target.parent.mkdir(parents=True,exist_ok=True)
        sha=hashlib.sha256(p.read_bytes()).hexdigest();old=p.relative_to(ROOT).as_posix()
        p.rename(target);assert hashlib.sha256(target.read_bytes()).hexdigest()==sha
        moves.append([old,target.relative_to(ROOT).as_posix(),sha,'move, bytes unchanged'])
    for p in list(ROOT.glob('*')):
        if not p.is_file():continue
        if p.suffix=='.docx':move(p,ROOT/'docs/reports'/p.name)
        elif p.suffix=='.pdf':move(p,ROOT/('docs/references' if 'DICE' in p.name else 'docs/reports/history')/p.name)
        elif p.name.endswith('_检查报告.md'):move(p,ROOT/'docs/reports'/p.name)
    handbook=next((ROOT/'docs/references').glob('DICE*.pdf'))
    for p in (ROOT/'robot_ws').rglob('DICE*.pdf'):
        if hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(handbook.read_bytes()).digest():
            moves.append([p.relative_to(ROOT).as_posix(),handbook.relative_to(ROOT).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest(),'deduplicate exact bytes; canonical PDF retained'])
            p.unlink()
    with (AUDIT/'file_moves.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['old_path','new_path','sha256','action']);w.writerows(moves)
    return moves
if __name__=='__main__':
    if '--organize' in __import__('sys').argv:organize()
    else:inventory()
