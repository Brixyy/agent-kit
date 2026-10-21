---
name: reactflow
description: >
  ReactFlow (@xyflow/react) best practices — coordinate systems, edges, handles, custom nodes,
  sub-flows, and obstacle-avoiding edge routing. Use this skill whenever working with ReactFlow
  components, editing files that import from @xyflow/react, creating or modifying custom nodes/edges,
  working with Handle components, debugging edge routing issues, or implementing graph visualizations.
  Triggers on: imports from @xyflow/react, ReactFlow component usage, Handle/Edge/Node types,
  SmartStepEdge, graph layout code, or any mention of "reactflow", "react flow", "xyflow".
---

# ReactFlow Best Practices

## Coordinate Systems

ReactFlow uses a single **canvas coordinate space** for all positioning. Understanding this prevents the #1 source of bugs.

**Nodes**: `position: { x, y }` is in canvas space (absolute coordinates).

**Child nodes** (`parentId` set): position is **relative to parent's top-left corner**. `{ x: 0, y: 0 }` = parent's top-left. ReactFlow internally converts to absolute canvas coords for rendering. You never need to do this conversion yourself.

**Edges**: Custom edge components receive `sourceX`, `sourceY`, `targetX`, `targetY` — these are **already in canvas space**. Use them directly in your SVG path. Do not add offsets, do not transform coordinates.

**Key rule**: If you find yourself manually adding parent positions to child positions, or computing coordinate offsets for edges — stop. ReactFlow handles all coordinate transformations internally.

## Edges

### Built-in Types
| Type | Description |
|------|-------------|
| `default` | Cubic bezier curve |
| `smoothstep` | Orthogonal with rounded corners |
| `step` | Orthogonal with sharp corners |
| `straight` | Direct line |

### smoothstep Options
```ts
pathOptions: {
  offset: 20,        // how far edge bends from direct path
  borderRadius: 5,   // corner roundness
}
```

### Obstacle Avoidance
ReactFlow has **no built-in obstacle avoidance** — edges will pass through nodes. For edges that route around nodes, use `@jalez/react-flow-smart-edge`:

```tsx
import { SmartStepEdge } from '@jalez/react-flow-smart-edge'

// Define OUTSIDE component
const edgeTypes = { smart: SmartStepEdge }

// In ReactFlow
<ReactFlow edgeTypes={edgeTypes} ... />

// On edges
{ type: 'smart', source: 'a', target: 'b' }
```

SmartStepEdge uses A* pathfinding on a grid, automatically routing around all nodes. It's reactive — recalculates on drag. Also available: `SmartBezierEdge`, `SmartStraightEdge`.

Config options via `getSmartEdge()`: `nodePadding` (default 10), `gridRatio` (default 10).

### Edge Labels
```ts
{
  label: 'my label',
  labelStyle: { fontSize: 9, fill: 'white' },
  labelBgStyle: { fill: 'rgba(0,0,0,0.8)' },
  labelBgPadding: [4, 6] as [number, number],
  labelBgBorderRadius: 4,
}
```

For custom label positioning, use `EdgeLabelRenderer` with absolute positioning:
```tsx
<EdgeLabelRenderer>
  <div style={{
    position: 'absolute',
    transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
    pointerEvents: 'all',
  }} className="nodrag nopan">
    {label}
  </div>
</EdgeLabelRenderer>
```

### Custom Edges
Use `BaseEdge` + utility functions — don't build SVG paths from scratch:
```tsx
import { BaseEdge, getSmoothStepPath, type EdgeProps } from '@xyflow/react'

function MyEdge(props: EdgeProps) {
  const [path, labelX, labelY] = getSmoothStepPath({
    sourceX: props.sourceX, sourceY: props.sourceY,
    targetX: props.targetX, targetY: props.targetY,
    sourcePosition: props.sourcePosition,
    targetPosition: props.targetPosition,
  })
  return <BaseEdge id={props.id} path={path} style={props.style} />
}
```

## Handles

### ID Convention
Use consistent prefixed IDs for clarity:
- `s-top`, `s-bottom`, `s-left`, `s-right` — source handles
- `t-top`, `t-bottom`, `t-left`, `t-right` — target handles

### Full Connectivity Pattern
For nodes that can connect from any direction, add **both source and target on each side** (8 handles total):

```tsx
<Handle type="source" id="s-top"    position={Position.Top}    />
<Handle type="target" id="t-top"    position={Position.Top}    />
<Handle type="source" id="s-bottom" position={Position.Bottom} />
<Handle type="target" id="t-bottom" position={Position.Bottom} />
<Handle type="source" id="s-left"   position={Position.Left}   />
<Handle type="target" id="t-left"   position={Position.Left}   />
<Handle type="source" id="s-right"  position={Position.Right}  />
<Handle type="target" id="t-right"  position={Position.Right}  />
```

### Edge ↔ Handle Matching
`sourceHandle` on the edge **must match** a handle `id` with `type="source"` on the source node. Same for `targetHandle` ↔ `type="target"`.

```ts
// Edge
{ source: 'nodeA', target: 'nodeB', sourceHandle: 's-bottom', targetHandle: 't-top' }
// nodeA must have: <Handle type="source" id="s-bottom" ... />
// nodeB must have: <Handle type="target" id="t-top" ... />
```

## Custom Nodes

### Performance Rules
Define `nodeTypes` and `edgeTypes` **outside** your component — if defined inside, React creates new objects on every render, causing all nodes/edges to re-mount:

```tsx
// GOOD — outside component
const nodeTypes = { custom: MyNode }
const edgeTypes = { smart: SmartStepEdge }

function MyFlow() {
  return <ReactFlow nodeTypes={nodeTypes} edgeTypes={edgeTypes} ... />
}
```

Wrap custom node components in `memo()` to prevent unnecessary re-renders.

### Interaction Classes
- `nodrag` — on interactive elements (inputs, buttons) inside nodes to prevent accidental drag
- `nopan` — on elements that should not trigger viewport panning

## Sub-flows (Child Nodes)

Child nodes have `parentId` set, making their position relative to the parent:

```ts
{ id: 'child', parentId: 'parent', position: { x: 10, y: 20 }, ... }
// Renders at parent.position + { x: 10, y: 20 } in canvas space
```

**Rules:**
- Parent node **must appear before children** in the nodes array
- `extent: 'parent'` prevents dragging outside parent
- Edges to/from child nodes work normally — ReactFlow handles the coordinate math
- The `group` node type is designed for parents (no handles, acts as container)

## Anti-patterns (From Real Mistakes)

These are patterns that caused real bugs in production. Each one cost hours of debugging:

| Don't | Why | Do Instead |
|-------|-----|------------|
| Write custom A* edge router | Coordinate space bugs, static paths that don't react to drag, hundreds of lines of fragile code | Use `SmartStepEdge` from `@jalez/react-flow-smart-edge` |
| Manually compute edge coordinates | sourceX/Y are already in canvas space | Use them directly, or use `getSmoothStepPath()` |
| Store path points in `edge.data` | Points become static — edges don't follow nodes on drag | Let ReactFlow compute paths dynamically |
| Define nodeTypes/edgeTypes inside component | Causes re-mount of all nodes/edges on every render | Define as module-level constants |
| Use `require()` for ReactFlow libs | Breaks with Turbopack/Vite | Use ES `import` |

### The Edge Routing Test
After implementing any edge changes, **drag a node**. If edges don't follow the node, your coordinate system is wrong. This simple test catches 90% of edge routing bugs.
