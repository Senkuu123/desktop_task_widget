"""
旧版版本信息生成脚本，已由tools/build/build_simple.py的内置生成器替代。
仅供历史参考；手动运行会覆盖tools/build/version_info.txt。
"""

import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
VERSION_INFO_PATH = PROJECT_DIR / 'tools' / 'build' / 'version_info.txt'

def create_version_info_file():
    """创建版本信息文件"""
    version_content = """# UTF-8
#
# 版本信息资源定义文件

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Personal'),
         StringStruct(u'FileDescription', u'Desktop Task Widget'),
         StringStruct(u'FileVersion', u'1.0.0.0'),
         StringStruct(u'InternalName', u'DesktopTaskWidget'),
         StringStruct(u'LegalCopyright', u'Copyright © 2024'),
         StringStruct(u'OriginalFilename', u'DesktopTaskWidget.exe'),
         StringStruct(u'ProductName', u'Desktop Task Widget'),
         StringStruct(u'ProductVersion', u'1.0.0.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [0x409, 1200])])
  ]
)
"""
    
    with open(VERSION_INFO_PATH, 'w', encoding='utf-8') as f:
        f.write(version_content)
    
    print(f"✅ 已创建版本信息文件: {VERSION_INFO_PATH}")
    
    # 验证文件是否存在
    if os.path.exists(VERSION_INFO_PATH):
        print(f"📁 文件大小: {os.path.getsize(VERSION_INFO_PATH)} 字节")
        return True
    else:
        print("❌ 创建版本信息文件失败")
        return False

if __name__ == '__main__':
    create_version_info_file()
