# CAD-LLM Prompt Enhancement Guide

## Original Prompt
```
a kitchen floor plan that has sink, gas burners and a center table
```

## Enhanced Prompts (Best to Worst)

### 1. Most Detailed (Recommended)
```
Create a kitchen floor plan with the following elements:
- A rectangular kitchen area: 4000mm x 3000mm (4m x 3m)
- A sink: rectangular shape, 600mm x 500mm, positioned along the north wall, centered
- Gas burners: 4 circular burners, each 150mm radius, arranged in a 2x2 grid, total area 800mm x 800mm, positioned on the west wall
- A center table: rectangular shape, 1200mm x 800mm, centered in the room at coordinates (2000, 1500)
- All elements should be drawn as closed shapes using lines
- Include walls as rectangular boundaries
- Center the entire floor plan at origin (0, 0)
```

### 2. Detailed with Relationships
```
Create a kitchen floor plan (4000mm x 3000mm) with:
- Sink (600mm x 500mm rectangle) on the north wall, centered
- Gas stove with 4 burners (each 150mm radius circles in 2x2 grid, total 800mm x 800mm) on the west wall
- Center table (1200mm x 800mm rectangle) in the middle of the room
- Draw all as separate closed shapes using lines and circles
- Include room boundaries as walls
- Center at origin
```

### 3. Structured Format
```
Kitchen floor plan:
Room: 4000mm x 3000mm rectangle, centered at origin
Sink: 600mm x 500mm rectangle, positioned at (2000, 2800) - north wall
Stove: 800mm x 800mm square with 4 circular burners (150mm radius each) at (400, 1500) - west wall
Table: 1200mm x 800mm rectangle at center (2000, 1500)
All shapes must be closed and use lines/circles
```

### 4. Simple but Specific
```
Create a kitchen floor plan 4m x 3m with:
- Rectangular sink 60cm x 50cm on north wall
- Gas stove 80cm x 80cm with 4 burners (15cm radius) on west wall  
- Center table 120cm x 80cm in middle
- Draw as separate closed shapes, centered at origin
```

### 5. Minimal Enhancement
```
Kitchen floor plan (4000mm x 3000mm) with sink (600x500mm), gas burners (4 circles, 150mm radius each in 800x800mm area), and center table (1200x800mm). Draw all as closed shapes, centered at origin.
```

## Key Enhancement Principles

### 1. Add Specific Dimensions
- ✅ "kitchen 4000mm x 3000mm" 
- ❌ "a kitchen"

### 2. Specify Element Sizes
- ✅ "sink 600mm x 500mm"
- ❌ "sink"

### 3. Define Spatial Relationships
- ✅ "sink on north wall, centered"
- ❌ "sink in kitchen"

### 4. Specify Shape Types
- ✅ "rectangular sink", "circular burners"
- ❌ "sink", "burners"

### 5. Include Layout Instructions
- ✅ "arranged in 2x2 grid"
- ❌ "gas burners"

### 6. Request Closed Shapes
- ✅ "draw as closed shapes using lines"
- ❌ (implicit)

### 7. Specify Centering
- ✅ "centered at origin (0, 0)"
- ❌ (may default incorrectly)

### 8. Use Architectural Terminology
- ✅ "floor plan", "walls", "room boundaries"
- ❌ "kitchen with stuff"

## Template for Kitchen Floor Plans

```
Create a kitchen floor plan with the following specifications:

Room Dimensions: [WIDTH]mm x [HEIGHT]mm
Room Position: Centered at origin (0, 0)

Elements:
1. Sink: [WIDTH]mm x [HEIGHT]mm rectangle, positioned at ([X], [Y]) - [WALL] wall
2. Stove: [WIDTH]mm x [HEIGHT]mm with [N] burners ([RADIUS]mm radius each), positioned at ([X], [Y]) - [WALL] wall
3. Table: [WIDTH]mm x [HEIGHT]mm rectangle, positioned at ([X], [Y]) - center

Requirements:
- Draw all elements as separate closed shapes
- Use lines for rectangular elements
- Use circles for burners
- Include room boundaries as walls
- All shapes must be closed
- Center the entire floor plan at origin
```

## Common Kitchen Element Dimensions (Reference)

- **Standard Kitchen**: 3000-5000mm x 2500-4000mm
- **Sink**: 600-900mm x 500-600mm
- **Stove**: 600-900mm x 600-900mm
- **Burner**: 100-200mm radius
- **Center Table**: 1000-1500mm x 700-1000mm
- **Counter Depth**: 600mm standard
- **Walkway**: Minimum 900mm clearance

## Example: Complete Kitchen Prompt

```
Create a detailed kitchen floor plan with these specifications:

Room: 4500mm x 3500mm rectangle, centered at origin (0, 0)
Walls: Draw room boundaries as rectangular walls

Elements (all as separate closed shapes):
1. Sink: 800mm x 600mm rectangle at (2250, 3200) - north wall, centered
2. Gas Stove: 900mm x 900mm square at (450, 1750) - west wall
   - 4 burners: circles, 180mm radius each
   - Burner positions: (600, 1500), (600, 2100), (750, 1500), (750, 2100)
3. Center Table: 1400mm x 900mm rectangle at (2250, 1750) - room center

Requirements:
- All shapes must be closed
- Use lines for rectangles
- Use circles for burners
- Include all walls as boundaries
- Center entire plan at origin
- Draw each element separately
```


