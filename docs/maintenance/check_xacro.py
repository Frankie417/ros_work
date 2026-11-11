from pathlib import Path
import sys,json,xml.dom.minidom as MD,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tmp/semester_qa_deps'))
import xacro
from catkin_pkg.package import parse_package
pkg=R/'arm2026_ws/src/marm_description'
parsed=parse_package(str(pkg));results=[]
for name in ['marm_z1_style','marm_z1_style_course_variant']:
    source=(pkg/'urdf'/f'{name}.xacro').read_text(encoding='utf8')
    source=source.replace('$(find marm_description)',pkg.as_posix())
    doc=MD.parseString(source);xacro.process_doc(doc)
    robot=ET.fromstring(doc.toxml());links=robot.findall('link');joints=robot.findall('joint')
    visual=len(robot.findall('.//visual'));collision=len(robot.findall('.//collision'))
    assert (len(links),len(joints),visual,collision)==(11,10,57,13)
    names={l.get('name') for l in links}
    assert all(j.find('parent').get('link') in names and j.find('child').get('link') in names for j in joints)
    results.append({'model':name,'links':len(links),'joints':len(joints),'visual':visual,'collision':collision})
result={'package':parsed.name,'runtime_dependencies':[d.name for d in parsed.run_depends],'xacro_version':'2.1.1 offline Python tool','package_find':'resolved to current package directory for static expansion only','models':results,'ROS_build_run':False}
(R/'docs/maintenance/xacro_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
