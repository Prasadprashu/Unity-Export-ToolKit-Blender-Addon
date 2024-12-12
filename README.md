# PrashuExportToolKit Blender Addon


## Overview

PrashuExportToolKit is a comprehensive Blender addon designed to streamline the export process for 3D models to game engines. It provides advanced export options and flexibility for game asset preparation.

## Features

- Multiple Export Formats
  - FBX export
  - OBJ export
- Export Modes
  - Single File Export: Export all selected objects in one file
  - Batch Export: Export each top-level object separately with its hierarchy
- Advanced Export Options
  - Modifier Application
  - Transformation Controls
    - Optional location application
    - Optional rotation application
    - Optional scale application
  - Mesh Triangulation

## Compatibility

- Blender Version: 4.0.0+

## Installation

1. Download the `Prashu_FBX_Export.py` file
2. In Blender, go to Edit > Preferences > Add-ons
3. Click "Install" and select the downloaded Python file
4. Enable the addon by checking the box next to "PrashuExportToolKit"

## Usage

### Export Panel Location
The export tools can be found in:
- 3D Viewport
- Sidebar (press 'N' to open)
- Tab: Export

### Export Settings

1. **Export Format**
   - Choose between FBX and OBJ formats
   
2. **Export Mode**
   - Single File: Export all selected objects in one file
   - Batch Export: Export each top-level object separately

3. **Advanced Options**
   - Apply Modifiers: Convert objects to mesh with current modifiers
   - Transformation Options:
     - Apply Location
     - Apply Rotation
     - Apply Scale
   - Triangulate Mesh: Convert quads to triangles for better game engine compatibility

### Export Process

1. Select the objects you want to export
2. Open the PrashuExportToolKit panel
3. Configure your export settings
4. Click "Export to Game Engine"
5. Choose your export location in the file browser

## Known Limitations

- Works best with mesh objects
- Hierarchy preservation depends on object selection
- Some complex modifier stacks might require manual intervention

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## License

This PrashuExportToolKit Blender addon is licensed under the terms of the [MIT License](https://opensource.org/licenses/MIT).

Copyright (C) 2  Prashu_Ammu_2129

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


## Author

Prashu_2129

## Version

1.6
