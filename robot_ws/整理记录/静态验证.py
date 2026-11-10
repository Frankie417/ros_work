"""只读静态归档检查：不导入、执行任何实验代码，不连接设备或网络。"""
from pathlib import Path
import ast
import csv
import hashlib
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import unquote

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT.parent
MODULES = ['01_robot_modeling_and_platform_setup', '02_robot_arm_motion_control',
           '03_visual_target_recognition_and_sorting', '04_gesture_recognition_and_interactive_manipulation']


def rows(name):
    with (PROJECT / '整理记录' / name).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    failures = []
    counts = {}
    for name, base, path_field in [('原始文件清单.csv', SOURCE, 'path'),
                                   ('复制文件校验.csv', PROJECT, 'target')]:
        items = rows(name)
        for item in items:
            path = base / item[path_field]
            if not path.is_file() or digest(path) != item['sha256']:
                failures.append({'kind': name, 'path': str(path)})
        counts[name] = len(items)

    image_rows = rows('图片来源.csv')
    for item in image_rows:
        target = PROJECT / item['target']
        if not target.is_file() or digest(target) != item['sha256']:
            failures.append({'kind': '图片提取字节', 'path': item['target']})
        source, member = item['source'].split('!/', 1)
        with zipfile.ZipFile(SOURCE / source) as archive:
            if hashlib.sha256(archive.read(member)).hexdigest() != item['sha256']:
                failures.append({'kind': '原报告图片来源', 'path': item['source']})
    counts['报告媒体来源记录'] = len(image_rows)

    archive_rows = rows('压缩包成员清单.csv')
    for item in archive_rows:
        if item['target'] and digest(PROJECT / item['target']) != item['sha256']:
            failures.append({'kind': 'ZIP提取', 'path': item['target']})
    counts['ZIP成员记录'] = len(archive_rows)
    counts['文件映射行数'] = len(rows('完整文件映射.csv'))
    if counts['文件映射行数'] != counts['原始文件清单.csv']:
        failures.append({'kind': '映射覆盖', 'path': '完整文件映射.csv'})

    syntax_files = notebook_cells = xml_files = links = notebook_links = 0
    for path in PROJECT.rglob('*'):
        if not path.is_file():
            continue
        if path.suffix == '.py':
            try:
                ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
                syntax_files += 1
            except SyntaxError as error:
                failures.append({'kind': 'Python语法', 'path': str(path), 'error': str(error)})
        elif path.suffix == '.ipynb':
            notebook = json.loads(path.read_text(encoding='utf-8-sig'))
            for index, cell in enumerate(notebook.get('cells', [])):
                if cell.get('cell_type') == 'markdown':
                    for target in re.findall(r'!?\[[^\]]*\]\(([^\n]+?)\)', ''.join(cell.get('source', []))):
                        if target.startswith(('https:', 'http:', 'mailto:', '#', 'data:')):
                            continue
                        target = unquote(target.split('#')[0].strip('<>'))
                        notebook_links += 1
                        if not (path.parent / target).exists():
                            failures.append({'kind': 'Notebook Markdown链接', 'path': str(path), 'cell': index, 'target': target})
                if cell.get('cell_type') != 'code':
                    continue
                try:
                    ast.parse(''.join(cell.get('source', [])), filename=f'{path}:cell{index}')
                    notebook_cells += 1
                except SyntaxError as error:
                    failures.append({'kind': 'Notebook语法', 'path': str(path), 'cell': index, 'error': str(error)})
        elif path.suffix in ('.xml', '.xacro', '.launch', '.urdf'):
            try:
                ET.parse(path)
                xml_files += 1
            except ET.ParseError as error:
                failures.append({'kind': 'XML语法', 'path': str(path), 'error': str(error)})
        elif path.suffix == '.md':
            body = re.sub(r'```[\s\S]*?```', '', path.read_text(encoding='utf-8-sig'))
            for target in re.findall(r'!?\[[^\]]*\]\(([^\n]+?)\)', body):
                if target.startswith(('https:', 'http:', 'mailto:', '#', 'data:')):
                    continue
                target = unquote(target.split('#')[0].strip('<>'))
                links += 1
                if not (path.parent / target).exists():
                    failures.append({'kind': 'Markdown链接', 'path': str(path.relative_to(PROJECT)), 'target': target})
    counts.update({'Python文件AST': syntax_files, 'Notebook代码Cell AST': notebook_cells,
                   'XML文件': xml_files, '本地Markdown链接及图片': links, 'Notebook内本地Markdown链接': notebook_links})

    for module in MODULES:
        for part in ('1.1_code', '1.2_readme', '1.3_experiment_results/figures',
                     '1.3_experiment_results/records', '1.3_experiment_results/original_reports'):
            if not (PROJECT / module / part).is_dir():
                failures.append({'kind': '目录结构', 'path': f'{module}/{part}'})
        for doc, expected in [('1.2_readme/README.md', 10), ('1.3_experiment_results/实验结果.md', 9)]:
            path = PROJECT / module / doc
            if not path.is_file() or len(re.findall(r'^## \d+\.', path.read_text(encoding='utf-8'), re.M)) != expected:
                failures.append({'kind': '文档章节', 'path': str(path)})

    urdf = PROJECT / MODULES[0] / '1.3_experiment_results/records/generated/marm.urdf'
    robot = ET.parse(urdf).getroot()
    link_names = {element.get('name') for element in robot.findall('link')}
    children = set()
    graph = {}
    for joint in robot.findall('joint'):
        parent, child = joint.find('parent').get('link'), joint.find('child').get('link')
        if parent not in link_names or child not in link_names or child in children:
            failures.append({'kind': 'URDF父子连接', 'path': joint.get('name')})
        children.add(child)
        graph.setdefault(parent, []).append(child)
    roots = link_names - children
    visited = set()

    def visit(name):
        if name in visited:
            failures.append({'kind': 'URDF环', 'path': name})
            return
        visited.add(name)
        for child in graph.get(name, []):
            visit(child)

    if len(roots) == 1:
        visit(next(iter(roots)))
    if len(roots) != 1 or visited != link_names:
        failures.append({'kind': 'URDF树完整性', 'path': str(urdf)})
    counts['URDF link/joint'] = [len(link_names), len(robot.findall('joint'))]

    result = {'scope': '静态检查；未导入或执行控制程序/Notebook，不启动ROS、网络或硬件',
              'counts': counts, 'failures': failures,
              'known_runtime_gaps': [
                  'catkin顶层CMake入口为路径文本；原模型两个launch的model参数无默认值',
                  '主marm.urdf无标准inertial，包未完整声明运行依赖',
                  '实体DICE SDK/config、本机虚拟环境、相机标定缺失',
                  '手势原始22条回执/录像及完整搬运任务链缺失']}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
