from pathlib import Path
import json
import time
import open3d as o3d
# ===================================================
# Get Project Paths
# ===================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FOLDER = PROJECT_ROOT / "part2" / "input"
json_file = INPUT_FOLDER / "item_list.json"

print(f"Reading file: {json_file}")

# ===================================================
# Read JSON
# ===================================================

with open(json_file, "r") as file:
    items = json.load(file)

print("✅ JSON loaded successfully!")
print(f"Total Items: {len(items)}")

# ===================================================
# Calculate Volume
# ===================================================

for item in items:
    length, width, height = item["dims"]
    item["volume"] = length * width * height

# ===================================================
# Sort Items (Largest → Smallest)
# ===================================================

items.sort(key=lambda item: item["volume"], reverse=True)

print("\n========== SORTED ITEMS ==========\n")

for item in items:
    print(
        f"ID: {item['id']:2d} | "
        f"Type: {item['type']:15s} | "
        f"Dimensions: {item['dims']} | "
        f"Volume: {item['volume']}"
    )

# ===================================================
# Master Box
# ===================================================

MASTER_LENGTH = 100
MASTER_WIDTH = 100
MASTER_HEIGHT = 100

current_x = 0
current_y = 0
current_z = 0

row_depth = 0
layer_height = 0

# ===================================================
# Collision Detection
# ===================================================

placed_items = []


def is_overlapping(pos1, size1, pos2, size2):
    """
    Returns True if two boxes overlap.
    """

    x1, y1, z1 = pos1
    l1, w1, h1 = size1

    x2, y2, z2 = pos2
    l2, w2, h2 = size2

    overlap_x = (x1 < x2 + l2) and (x1 + l1 > x2)
    overlap_y = (y1 < y2 + w2) and (y1 + w1 > y2)
    overlap_z = (z1 < z2 + h2) and (z1 + h1 > z2)

    return overlap_x and overlap_y and overlap_z


print("\n========== ITEM PLACEMENTS ==========\n")

# ===================================================
# Place Items
# ===================================================

for item in items:

    length, width, height = item["dims"]

    # New Row
    if current_x + length > MASTER_LENGTH:
        current_x = 0
        current_y += row_depth
        row_depth = 0

    # New Layer
    if current_y + width > MASTER_WIDTH:
        current_x = 0
        current_y = 0
        current_z += layer_height
        layer_height = 0

    # Master Box Full
    if current_z + height > MASTER_HEIGHT:
        print(f"❌ Item {item['id']} cannot fit inside the Master Box.")
        continue

    # Proposed Position
    position = (current_x, current_y, current_z)

    # Collision Check
    collision = False

    for placed in placed_items:
        if is_overlapping(
            position,
            item["dims"],
            placed["position"],
            placed["dims"],
        ):
            collision = True
            break

    if collision:
        print(f"❌ Collision detected for Item {item['id']}")
        continue

    # Save Position
    item["position"] = position

    placed_items.append(
        {
            "position": position,
            "dims": item["dims"],
        }
    )

    print(
        f"Item {item['id']:2d} "
        f"({item['type']}) "
        f"-> Position {position}"
    )

    # Move Along X-axis
    current_x += length

    # Update Row Depth
    row_depth = max(row_depth, width)

    # Update Layer Height
    layer_height = max(layer_height, height)

print("\n✅ Coordinate generation completed!")
# ===================================================
# Open3D Visualization
# ===================================================

print("\nOpening Open3D visualization...")

# Create visualizer
vis = o3d.visualization.Visualizer()
vis.create_window(window_name="3D Packing", width=1200, height=800)

# ---------------------------------------------------
# Create Master Box
# ---------------------------------------------------

# ---------------------------------------------------
# Create Wireframe Master Box
# ---------------------------------------------------

points = [
    [0, 0, 0],
    [MASTER_LENGTH, 0, 0],
    [MASTER_LENGTH, MASTER_WIDTH, 0],
    [0, MASTER_WIDTH, 0],
    [0, 0, MASTER_HEIGHT],
    [MASTER_LENGTH, 0, MASTER_HEIGHT],
    [MASTER_LENGTH, MASTER_WIDTH, MASTER_HEIGHT],
    [0, MASTER_WIDTH, MASTER_HEIGHT],
]

lines = [
    [0,1], [1,2], [2,3], [3,0],   # Bottom
    [4,5], [5,6], [6,7], [7,4],   # Top
    [0,4], [1,5], [2,6], [3,7]    # Vertical
]

colors = [[0, 0, 0] for _ in lines]   # Black lines

master_box = o3d.geometry.LineSet()
master_box.points = o3d.utility.Vector3dVector(points)
master_box.lines = o3d.utility.Vector2iVector(lines)
master_box.colors = o3d.utility.Vector3dVector(colors)

vis.add_geometry(master_box)

# ---------------------------------------------------
# Add Items One by One
# ---------------------------------------------------

TYPE_COLORS = {
    "large_crate":   [1, 0, 0],      # Red
    "flat_panel":    [0, 1, 0],      # Green
    "standard_box":  [0, 0, 1],      # Blue
    "flat_box":      [1, 1, 0],      # Yellow
    "long_beam":     [1, 0, 1],      # Purple
    "long_box":      [1, 0.5, 0],    # Orange
    "medium_cube":   [0, 1, 1],      # Cyan
    "small_filler":  [0.7, 0.7, 0.7] # Gray
}

for index, item in enumerate(items):

    print(
        f"Placing Item {item['id']} "
        f"({item['type']}) "
        f"at {item['position']}"
    )

    length, width, height = item["dims"]
    x, y, z = item["position"]

    cube = o3d.geometry.TriangleMesh.create_box(
        width=length,
        height=width,
        depth=height
    )

    cube.translate((x, y, z))

    cube.paint_uniform_color(TYPE_COLORS[item["type"]])

    vis.add_geometry(cube)

    vis.poll_events()
    vis.update_renderer()

    time.sleep(0.8)

print("Animation finished.")

vis.run()
vis.destroy_window()