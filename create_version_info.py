"""
创建版本信息文件
"""

import os

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
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_content)
    
    print("✅ 已创建版本信息文件: version_info.txt")
    
    # 验证文件是否存在
    if os.path.exists('version_info.txt'):
        print(f"📁 文件大小: {os.path.getsize('version_info.txt')} 字节")
        return True
    else:
        print("❌ 创建版本信息文件失败")
        return False

if __name__ == '__main__':
    create_version_info_file()