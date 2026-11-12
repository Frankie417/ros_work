"""Read-only syntax, links, resources and package hash checks; no hardware imports."""
from pathlib import Path
from urllib.parse import unquote
import ast,csv,hashlib,json,re,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
errors=[];counts={'python':0,'notebooks':0,'code_cells':0,'xml':0,'markdown_links':0};known=[]
for p in R.rglob('*'):
    if not p.is_file() or set(p.parts)&{'__pycache__','.venv-gesture','build','devel','install','.ipynb_checkpoints','runtime'}:continue
    try:
        if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'));counts['python']+=1
        if p.suffix=='.ipynb':
            o=json.loads(p.read_text(encoding='utf-8-sig'));assert o.get('nbformat')==4;counts['notebooks']+=1
            for c in o['cells']:
                s=''.join(c.get('source',[]))
                if c['cell_type']=='code':ast.parse(s);counts['code_cells']+=1
                if c['cell_type']=='markdown':
                    for u in re.findall(r'!?\[[^\]]*\]\(([^\n]+?)\)',s)+re.findall(r'(?:src|href)=[\"\']([^\"\']+)',s):
                        if u.startswith(('http:','https:','#','attachment:','data:')):continue
                        q=(p.parent/unquote(u)).resolve()
                        if not q.exists():
                            if p.name.startswith('05.') and re.fullmatch(r'\./image/p[1235678]\.jpg',u):known.append(u)
                            else:errors.append([p.relative_to(R).as_posix(),u])
        if p.suffix in {'.xml','.launch','.urdf','.xacro'}:ET.parse(p);counts['xml']+=1
        if p.suffix=='.md':
            for u in re.findall(r'!?\[[^\]]*\]\(([^\n]+?)\)',p.read_text(encoding='utf8')):
                if u.startswith(('http:','https:','#','mailto:','data:')):continue
                q=(p.parent/unquote(u.split('#')[0].strip('<>'))).resolve();counts['markdown_links']+=1
                if not q.is_relative_to(R) or not q.exists():errors.append([p.relative_to(R).as_posix(),u])
    except Exception as e:errors.append([p.relative_to(R).as_posix(),str(e)])
model=R/'src/gesture_control/week7/models/gesture_recognizer.task'
if not model.exists() or model.read_bytes().startswith(b'version https://git-lfs.github.com/spec'):errors.append(['gesture model','missing or LFS pointer'])
with (R/'docs/文件清单.csv').open(encoding='utf-8-sig',newline='') as f:
    for row in csv.DictReader(f):
        p=R/row['homework_path']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['final_sha256']:errors.append([row['homework_path'],'final SHA-256 mismatch'])
print(json.dumps({'counts':counts,'known_original_missing_images':known,'errors':errors,'hardware_run':False},ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
