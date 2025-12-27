#!/usr/bin/env python3
"""
Generate enhanced CAD dataset for training.

This script creates a dataset where:
- Instruction: Simple user prompts (e.g., "a kitchen floor plan that has sink, gas burners and a center table")
- Output: Enhanced detailed descriptions (e.g., "Kitchen floor plan (4000mm x 3000mm) with: Sink: 600mm x 500mm rectangle...")

Target: 200,000+ examples
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

# Room types and their elements
ROOM_TEMPLATES = {
    "kitchen": {
        "room_sizes": [(3000, 2500), (3500, 3000), (4000, 3000), (4500, 3500), (5000, 4000)],
        "elements": {
            "sink": {
                "sizes": [(600, 500), (700, 550), (800, 600), (900, 600)],
                "positions": ["north wall", "south wall", "east wall", "west wall", "island"],
                "shapes": ["rectangle"]
            },
            "stove": {
                "sizes": [(600, 600), (700, 700), (800, 800), (900, 900)],
                "positions": ["north wall", "south wall", "east wall", "west wall", "island"],
                "shapes": ["square"],
                "burners": [2, 4, 6],
                "burner_radius": [120, 150, 180, 200]
            },
            "refrigerator": {
                "sizes": [(600, 700), (700, 800), (800, 900)],
                "positions": ["north wall", "south wall", "east wall", "west wall"],
                "shapes": ["rectangle"]
            },
            "table": {
                "sizes": [(1000, 700), (1200, 800), (1400, 900), (1600, 1000)],
                "positions": ["center", "middle"],
                "shapes": ["rectangle", "oval"]
            },
            "island": {
                "sizes": [(1200, 800), (1500, 1000), (1800, 1200)],
                "positions": ["center"],
                "shapes": ["rectangle"]
            },
            "cabinet": {
                "sizes": [(600, 600), (800, 600), (1000, 600)],
                "positions": ["north wall", "south wall", "east wall", "west wall"],
                "shapes": ["rectangle"]
            }
        }
    },
    "bedroom": {
        "room_sizes": [(3000, 3000), (3500, 3500), (4000, 3500), (4500, 4000), (5000, 4500)],
        "elements": {
            "bed": {
                "sizes": [(900, 2000), (1000, 2000), (1200, 2000), (1500, 2000), (1800, 2000)],
                "positions": ["north wall", "south wall", "east wall", "west wall", "center"],
                "shapes": ["rectangle"]
            },
            "wardrobe": {
                "sizes": [(1200, 600), (1500, 600), (1800, 600), (2000, 600)],
                "positions": ["north wall", "south wall", "east wall", "west wall"],
                "shapes": ["rectangle"]
            },
            "desk": {
                "sizes": [(1200, 600), (1500, 700), (1800, 800)],
                "positions": ["north wall", "south wall", "east wall", "west wall", "center"],
                "shapes": ["rectangle"]
            },
            "window": {
                "sizes": [(800, 1200), (1000, 1500), (1200, 1800)],
                "positions": ["north wall", "south wall", "east wall", "west wall"],
                "shapes": ["rectangle"]
            },
            "door": {
                "sizes": [(800, 2000), (900, 2100)],
                "positions": ["north wall", "south wall", "east wall", "west wall"],
                "shapes": ["rectangle"]
            }
        }
    },
    "living room": {
        "room_sizes": [(4000, 4000), (4500, 4500), (5000, 4500), (6000, 5000)],
        "elements": {
            "sofa": {
                "sizes": [(1800, 900), (2000, 1000), (2400, 1000), (3000, 1000)],
                "positions": ["north wall", "south wall", "east wall", "west wall", "center"],
                "shapes": ["rectangle"]
            },
            "coffee table": {
                "sizes": [(1000, 600), (1200, 700), (1500, 800)],
                "positions": ["center", "middle"],
                "shapes": ["rectangle", "oval", "circle"]
            },
            "tv stand": {
                "sizes": [(1200, 400), (1500, 500), (1800, 600)],
                "positions": ["north wall", "south wall", "east wall", "west wall"],
                "shapes": ["rectangle"]
            },
            "window": {
                "sizes": [(1500, 1500), (2000, 1800), (2500, 2000)],
                "positions": ["north wall", "south wall", "east wall", "west wall"],
                "shapes": ["rectangle"]
            }
        }
    },
    "bathroom": {
        "room_sizes": [(2000, 2000), (2500, 2000), (3000, 2500)],
        "elements": {
            "toilet": {
                "sizes": [(400, 700), (450, 750)],
                "positions": ["north wall", "south wall", "east wall", "west wall"],
                "shapes": ["rectangle"]
            },
            "sink": {
                "sizes": [(500, 400), (600, 450), (600, 500)],
                "positions": ["north wall", "south wall", "east wall", "west wall"],
                "shapes": ["rectangle", "oval"]
            },
            "shower": {
                "sizes": [(900, 900), (1000, 1000), (1200, 1200)],
                "positions": ["corner", "north wall", "south wall", "east wall", "west wall"],
                "shapes": ["square", "rectangle"]
            },
            "bathtub": {
                "sizes": [(1500, 700), (1700, 800), (1800, 900)],
                "positions": ["north wall", "south wall", "east wall", "west wall"],
                "shapes": ["rectangle", "oval"]
            }
        }
    }
}

# Simple shape templates
SIMPLE_SHAPES = {
    "circle": {
        "prompts": [
            "a circle",
            "create a circle",
            "draw a circle",
            "a circular shape",
            "make a circle"
        ],
        "radii": [10, 20, 30, 40, 50, 60, 75, 100, 125, 150, 200, 250, 300, 400, 500]
    },
    "rectangle": {
        "prompts": [
            "a rectangle",
            "create a rectangle",
            "draw a rectangle",
            "a rectangular shape",
            "make a rectangle"
        ],
        "sizes": [
            (50, 30), (100, 50), (100, 75), (150, 100), (200, 100), (200, 150),
            (300, 200), (400, 300), (500, 400), (600, 500), (800, 600), (1000, 800)
        ]
    },
    "square": {
        "prompts": [
            "a square",
            "create a square",
            "draw a square",
            "a square shape",
            "make a square"
        ],
        "sizes": [50, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000]
    },
    "triangle": {
        "prompts": [
            "a triangle",
            "create a triangle",
            "draw a triangle",
            "a triangular shape",
            "make a triangle"
        ],
        "sizes": [
            (100, 100), (150, 150), (200, 200), (300, 300), (400, 400), (500, 500)
        ]
    }
}


def generate_room_description(room_type: str, elements: List[str], room_size: Tuple[int, int]) -> str:
    """Generate enhanced description for a room with elements."""
    width, height = room_size
    
    description_parts = [f"{room_type.capitalize()} floor plan ({width}mm x {height}mm) with:"]
    
    element_descriptions = []
    for element_name in elements:
        if element_name not in ROOM_TEMPLATES[room_type]["elements"]:
            continue
            
        element = ROOM_TEMPLATES[room_type]["elements"][element_name]
        size = random.choice(element["sizes"])
        position = random.choice(element["positions"])
        shape = random.choice(element["shapes"])
        
        if element_name == "stove" and "burners" in element:
            num_burners = random.choice(element["burners"])
            burner_radius = random.choice(element["burner_radius"])
            element_desc = (
                f"- {element_name.capitalize()}: {size[0]}mm x {size[1]}mm {shape} "
                f"with {num_burners} burners ({burner_radius}mm radius circles) on {position}"
            )
        else:
            if len(size) == 2:
                element_desc = (
                    f"- {element_name.capitalize()}: {size[0]}mm x {size[1]}mm {shape} on {position}"
                )
            else:
                element_desc = (
                    f"- {element_name.capitalize()}: {size}mm {shape} on {position}"
                )
        
        element_descriptions.append(element_desc)
    
    description_parts.extend(element_descriptions)
    description_parts.append("- Draw all as separate closed shapes, include walls, centered at origin")
    
    return "\n".join(description_parts)


def generate_simple_prompt(room_type: str, elements: List[str]) -> str:
    """Generate a simple user prompt."""
    element_str = ", ".join(elements)
    prompts = [
        f"a {room_type} floor plan that has {element_str}",
        f"create a {room_type} with {element_str}",
        f"draw a {room_type} floor plan with {element_str}",
        f"a {room_type} that includes {element_str}",
        f"design a {room_type} floor plan with {element_str}",
    ]
    return random.choice(prompts)


def generate_simple_shape_description(shape_type: str, size) -> Tuple[str, str]:
    """Generate simple prompt and enhanced description for basic shapes."""
    prompt_template = random.choice(SIMPLE_SHAPES[shape_type]["prompts"])
    
    if shape_type == "circle":
        radius = size
        prompt = f"{prompt_template} with radius {radius}mm"
        description = f"Circle with radius {radius}mm, centered at origin (0, 0)"
    elif shape_type == "square":
        side = size
        prompt = f"{prompt_template} with side {side}mm"
        description = f"Square with side {side}mm, centered at origin (0, 0)"
    elif shape_type == "rectangle":
        width, height = size
        prompt = f"{prompt_template} {width}mm x {height}mm"
        description = f"Rectangle {width}mm x {height}mm, centered at origin (0, 0)"
    elif shape_type == "triangle":
        base, height = size
        prompt = f"{prompt_template} with base {base}mm and height {height}mm"
        description = f"Triangle with base {base}mm and height {height}mm, centered at origin (0, 0)"
    else:
        prompt = prompt_template
        description = f"{shape_type.capitalize()} shape, centered at origin (0, 0)"
    
    return prompt, description


def generate_room_examples(num_examples: int) -> List[Dict]:
    """Generate room floor plan examples."""
    examples = []
    
    for _ in range(num_examples):
        room_type = random.choice(list(ROOM_TEMPLATES.keys()))
        room_template = ROOM_TEMPLATES[room_type]
        
        # Select random room size
        room_size = random.choice(room_template["room_sizes"])
        
        # Select 2-5 random elements
        available_elements = list(room_template["elements"].keys())
        num_elements = random.randint(2, min(5, len(available_elements)))
        selected_elements = random.sample(available_elements, num_elements)
        
        # Generate simple prompt
        simple_prompt = generate_simple_prompt(room_type, selected_elements)
        
        # Generate enhanced description
        enhanced_description = generate_room_description(room_type, selected_elements, room_size)
        
        examples.append({
            "instruction": simple_prompt,
            "output": enhanced_description
        })
    
    return examples


def generate_simple_shape_examples(num_examples: int) -> List[Dict]:
    """Generate simple shape examples."""
    examples = []
    
    for _ in range(num_examples):
        shape_type = random.choice(list(SIMPLE_SHAPES.keys()))
        shape_template = SIMPLE_SHAPES[shape_type]
        
        if shape_type == "circle":
            size = random.choice(shape_template["radii"])
        elif shape_type == "square":
            size = random.choice(shape_template["sizes"])
        else:
            size = random.choice(shape_template["sizes"])
        
        prompt, description = generate_simple_shape_description(shape_type, size)
        
        examples.append({
            "instruction": prompt,
            "output": description
        })
    
    return examples


def generate_combined_examples(num_examples: int) -> List[Dict]:
    """Generate examples with multiple simple shapes."""
    examples = []
    
    shape_types = list(SIMPLE_SHAPES.keys())
    
    for _ in range(num_examples):
        num_shapes = random.randint(2, 4)
        selected_shapes = random.sample(shape_types, num_shapes)
        
        prompt_parts = []
        description_parts = []
        
        for shape_type in selected_shapes:
            shape_template = SIMPLE_SHAPES[shape_type]
            
            if shape_type == "circle":
                size = random.choice(shape_template["radii"])
                prompt_parts.append(f"{random.choice(shape_template['prompts'])} with radius {size}mm")
                description_parts.append(f"- Circle: {size}mm radius, centered")
            elif shape_type == "square":
                size = random.choice(shape_template["sizes"])
                prompt_parts.append(f"{random.choice(shape_template['prompts'])} with side {size}mm")
                description_parts.append(f"- Square: {size}mm x {size}mm")
            else:
                size = random.choice(shape_template["sizes"])
                if isinstance(size, tuple):
                    prompt_parts.append(f"{random.choice(shape_template['prompts'])} {size[0]}mm x {size[1]}mm")
                    description_parts.append(f"- {shape_type.capitalize()}: {size[0]}mm x {size[1]}mm")
                else:
                    prompt_parts.append(f"{random.choice(shape_template['prompts'])} {size}mm")
                    description_parts.append(f"- {shape_type.capitalize()}: {size}mm")
        
        prompt = f"create {', '.join(prompt_parts)}"
        description = "Multiple shapes:\n" + "\n".join(description_parts) + "\n- All shapes centered at origin (0, 0)"
        
        examples.append({
            "instruction": prompt,
            "output": description
        })
    
    return examples


def main():
    """Generate enhanced dataset."""
    output_path = Path(__file__).parent.parent / "jsonl" / "cadllm_enhanced.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    target_count = 200000
    
    print(f"Generating {target_count:,} enhanced CAD examples...")
    print("=" * 80)
    
    all_examples = []
    
    # Generate room examples (60% of dataset)
    print(f"Generating room floor plan examples...")
    room_examples = generate_room_examples(int(target_count * 0.6))
    all_examples.extend(room_examples)
    print(f"  ✅ Generated {len(room_examples):,} room examples")
    
    # Generate simple shape examples (25% of dataset)
    print(f"Generating simple shape examples...")
    shape_examples = generate_simple_shape_examples(int(target_count * 0.25))
    all_examples.extend(shape_examples)
    print(f"  ✅ Generated {len(shape_examples):,} shape examples")
    
    # Generate combined examples (15% of dataset)
    print(f"Generating combined shape examples...")
    combined_examples = generate_combined_examples(int(target_count * 0.15))
    all_examples.extend(combined_examples)
    print(f"  ✅ Generated {len(combined_examples):,} combined examples")
    
    # Shuffle examples
    random.shuffle(all_examples)
    
    # Write to file
    print(f"\nWriting {len(all_examples):,} examples to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"✅ Dataset created successfully!")
    print(f"   Total examples: {len(all_examples):,}")
    print(f"   File: {output_path}")
    print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    import random
    random.seed(42)  # For reproducibility
    main()

