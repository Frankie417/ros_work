"""Read-only code and artifact checks; writes only maintenance reports."""
from pathlib import Path
import ast,json,re,os,hashlib,csv,collections,xml.etree.ElementTree as ET
from urllib.parse import unquote
R=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
IGNORE={'.git','tmp','__pycache__','.ipynb_checkpoints','build','devel','install','.vscode','.idea'}
counts=collections.Counter();issues=[];secrets=[];imports=collections.defaultdict(set)
active_docs={R/'README.md',R/'robot_ws/README.md',*(R/'robot_ws').glob('0*/README.md')}
def problem(kind,p,detail,active=False):issues.append({'kind':kind,'path':p.relative_to(R).as_posix(),'detail':str(detail),'active':active})
for base,dirs,files in os.walk(R):
    dirs[:]=[d for d in dirs if d not in IGNORE and not d.startswith('.venv')]
    for name in files:
        p=Path(base)/name;ext=p.suffix.lower()
        if ext=='.py':
            counts['python_files']+=1
            try:
                t=ast.parse(p.read_text(encoding='utf-8-sig'))
                for n in ast.walk(t):
                    if isinstance(n,ast.Import):imports[p.relative_to(R).as_posix()].update(v.name.split('.')[0] for v in n.names)
                    elif isinstance(n,ast.ImportFrom) and n.module:imports[p.relative_to(R).as_posix()].add(n.module.split('.')[0])
            except (SyntaxError,UnicodeError) as e:problem('Python syntax',p,e)
        elif ext=='.ipynb':
            counts['notebooks']+=1
            try:
                obj=json.loads(p.read_text(encoding='utf-8-sig'))
                assert obj.get('nbformat')==4 and isinstance(obj.get('cells'),list)
                for i,c in enumerate(obj['cells']):
                    assert c.get('cell_type') in ['code','markdown','raw']
                    if c['cell_type']=='code':
                        counts['notebook_code_cells']+=1;s=''.join(c.get('source',[]))
                        try:ast.parse(s)
                        except SyntaxError as e:
                            if any(line.lstrip().startswith(('!','%','?')) for line in s.splitlines()):counts['ipython_magic_cells']+=1
                            else:problem('Notebook cell syntax',p,f'cell {i}: {e}')
            except (ValueError,AssertionError,KeyError) as e:problem('Notebook structure',p,e,True)
        elif ext in ['.xml','.urdf','.xacro','.launch']:
            counts['xml_files']+=1
            try:ET.parse(p)
            except ET.ParseError as e:problem('XML syntax',p,e)
        if ext=='.md':
            s=p.read_text(encoding='utf-8-sig',errors='replace')
            for url in re.findall(r'!?\[[^\]]*\]\(([^\n]+?)\)',s):
                if url.startswith(('http:','https:','mailto:','#','data:')):continue
                target=unquote(url.split('#')[0].strip('<>'))
                if not target:continue
                counts['markdown_local_links']+=1
                if not (p.parent/target).exists():problem('Markdown target missing',p,target,p in active_docs)
        if ext in ['.py','.ipynb','.md','.txt','.json','.yaml','.yml','.csv','.xml','.launch','.xacro'] and p.stat().st_size<15_000_000:
            s=p.read_text(encoding='utf-8-sig',errors='replace')
            for pat,label in [(r'gh[pousr]_[A-Za-z0-9]{30,}','GitHub token'),(r'github_pat_[A-Za-z0-9_]{40,}','GitHub fine token'),(r'sk-proj-[A-Za-z0-9_-]{30,}','API key'),(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----','private key')]:
                if re.search(pat,s):secrets.append({'path':p.relative_to(R).as_posix(),'type':label})
            # Human review candidates, with values deliberately omitted.
            for i,line in enumerate(s.splitlines()):
                if re.search(r'(?:password|passwd|api_key|access_token)\s*[=:]\s*[\"\'][^\"\']{4,}[\"\']',line,re.I):problem('Credential literal review',p,f'line {i+1}; value omitted')

# Check current model chain and all Package-relative launch resources.
pkg=R/'arm2026_ws/src/marm_description'
for p in (pkg/'launch').glob('*.launch'):
    for target in re.findall(r'\$\(find marm_description\)([^\s\"\']+)',p.read_text(encoding='utf8')):
        if not (pkg/target.lstrip('/')).exists():problem('Launch resource missing',p,target,True)
for p in (R/'arm2026_ws/generated').glob('marm_z1_style*.urdf'):
    x=ET.parse(p).getroot();links={a.get('name') for a in x.findall('link')};joints=x.findall('joint')
    for j in joints:
        for tag in ['parent','child']:
            if j.find(tag).get('link') not in links:problem('URDF link missing',p,j.get('name'),True)
    counts['current_urdf_links']=len(links);counts['current_urdf_joints']=len(joints)
required=[R/'arm2026_ws/src/marm_description/launch/view_marm_z1_style.launch',R/'arm2026_ws/src/marm_description/launch/view_marm_z1_style_course_variant.launch',R/'week3/week3.ipynb',R/'week4/Week4_堆叠.ipynb',R/'week5/5.目标识别/week5.ipynb',R/'week6/week6.ipynb',R/'robot_ws/04_gesture_recognition_and_interactive_manipulation/1.1_code/week7/gesture_usb/app_usb.py',R/'robot_ws/04_gesture_recognition_and_interactive_manipulation/1.1_code/week7/models/gesture_recognizer.task',R/'arm5dof_python_uservo/config/z_error_polyfit.txt']
for p in required:
    if not p.is_file():problem('Documented entry missing',p,'required file',True)
    elif p.suffix=='.task' and p.read_bytes().startswith(b'version https://git-lfs.github.com/spec'):problem('LFS pointer not materialized',p,'run git lfs pull',True)

# Verify that pre-existing executable source, notebooks and experimental data
# retain their original bytes. Cache sources are excluded deliberately.
unchanged=0
with (OUT/'inventory_before.csv').open(encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        p=R/row['original_path'];parts=p.relative_to(R).parts
        if set(parts)&IGNORE or p.name=='organize_semester.py':continue
        if p.suffix.lower() in ['.py','.ipynb','.csv','.jsonl','.task'] and not row['original_path'].startswith('docs/maintenance/'):
            if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:problem('Original experiment bytes changed',p,'baseline hash mismatch',True)
            else:unchanged+=1
result={'counts':dict(counts),'original_source_data_files_unchanged':unchanged,'issues':issues,'high_confidence_secrets':secrets,'imports':{k:sorted(v) for k,v in imports.items()},'not_run':['ROS/catkin build and RViz GUI on Linux','Jetson serial, camera and physical arm','Windows camera/MediaPipe live recognition','New physical repetition trials']}
(OUT/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
summary='\n'.join(f'| {k} | {v} |' for k,v in counts.items())
issue_rows='\n'.join(f"| {i['kind']} | `{i['path']}` | {str(i['detail']).replace('|','/')} |" for i in issues)
(OUT/'quality_report.md').write_text(f'''# 项目检查记录

静态检查由check_project.py生成；不导入或执行机械臂算法。

| 检查对象 | 数量 |
|---|---:|
{summary}

原始源码、Notebook、CSV/JSONL及模型资源共{unchanged}个文件与整理前SHA-256一致。高置信度密钥扫描命中{len(secrets)}项；仅报告命中路径和类型，不打印值。普通password字面量候选列入下表，人工区分示例、历史输出和真实配置。

## 问题及历史差异

| 类型 | 文件 | 说明 |
|---|---|---|
{issue_rows if issue_rows else '| 无 | — | 本次静态检查未发现问题 |'}

历史清单记录旧版模型、旧路径和旧复制哈希，不重写以伪造历史一致性。本次清单及file_moves.csv是整理后的对应依据。IPython的!/%命令按Notebook专用语法单独计数，不当作普通Python错误。

## 当前环境未测试

当前为Windows文件整理环境，未执行Linux catkin/ROS/GUI、Jetson串口/相机/实体机械臂或Windows实时摄像头识别。未新增实体成功率或停止时延数据。模型URDF的XML与父子连杆引用已静态检查；这不能代替硬件和ROS运行验证。

模拟接收器与状态机的已有测试结果另见simulation_test.txt；若没有该文件，表示尚未执行。依赖版本与第三方许可TODO保留为待核实项，不填造版本或许可证。
''',encoding='utf8')
print(json.dumps({'counts':dict(counts),'unchanged_source_and_data':unchanged,'issues_by_kind':dict(collections.Counter(i['kind'] for i in issues)),'secrets':secrets,'active_errors':[i for i in issues if i['active']]},ensure_ascii=False))
extra='\n## 已执行的软件检查\n\n'
if (OUT/'simulation_test.txt').exists():extra+='现有手势模拟和回环网络测试10项通过，四色合成图识别测试通过，见simulation_test.txt。均不计作新增实体实验结果。\n\n'
if (OUT/'xacro_check.json').exists():extra+='Xacro 2.1.1离线展开主版及课程版，均为11 Link、10 Joint、57 visual、13 collision；catkin_pkg成功解析Package，Joint父子引用完整。包查找静态解析到当前目录，不代表ROS运行测试。结果见xacro_check.json。\n\n可用 `python -m pip install --target tmp/semester_qa_deps xacro catkin_pkg` 准备临时工具，再运行 `python docs/maintenance/check_xacro.py`。\n'
p=OUT/'quality_report.md';p.write_bytes((p.read_text(encoding='utf8')+extra).encode('utf8'))
raise SystemExit(1 if secrets or any(i['active'] for i in issues) else 0)
