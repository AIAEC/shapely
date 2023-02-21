# Stretch model of version 3

## Basic concepts
1. Pivot: the points that are used in stretch model.
2. Edge: direct edge, the edge that goes from one pivot to another.
3. EdgeSeq: helper class. the sequence of edges that are used to denote a sequence of direct edge,
   with one connected with the next. EdgeSeq could be a chain loop of edges.
4. Closure: the closure made by chain loops of edges. It might have 0 or more holes.
5. Stretch: the collection of pivots, edges, edgeSeqs and closures, which is the entry point of stretch model.
---

## Resource Operation
### Resource Relationship
Ownership:
```
Stretch───────┬────────┐
   │          │        │
   │          │        │
   ▼          ▼        ▼
Closure────►Edge────►Pivot

```

Back reference:
```
Stretch◄───────────────┐
 ▲ ▲                   │
 │ └─────────┐         │
 │           │         │
Closure◄────Edge◄────Pivot
```

> **Operation Principle**:
> 1. when we change ownership, modify the back ref as well.
> 2. when we change back reference, assert the ownership is correct.

For content below, we define the resource owned as **child** resource, and resource owning others as **parent**.
e.g. Edge owns Pivot, thus Edge is parent, Pivot is child.
---

### Deepcopy schema:
Copy resource as well as its children resource, and update the back ref of children resource to the copied parent.
Deepcopy should not alter the current resource's back ref.

e.g. when we deepcopy an edge, we deepcopy its pivots, and update the back ref of the pivot to the copied edge, but
this copied edge should have ref to origin closure and stretch

e.g. when we deepcopy a stretch, we deepcopy all its resource, including pivots, edges and closures, and make the
back ref between these children resources right.

---
### Validity of Resource
Closure's exterior and interior can hold cracks.
For exterior:
```
┌─────────┐      ┌─────────┐
│         │      │         │
│    │    │      │         ├────
│    │    │      │         │
└────┴────┘      └─────────┘
valid           invalid
```

For interior:
```
┌─────────────────┐     ┌────────────────┐     ┌─────────────────┐
│  ┌───────────┐  │     │                │     │  ┌───────────┐  │
│  │           │  │     │   │            │     │  │           │  │
│  │           │  │     │   │            │     │  │     │     │  │
│  └─────┬─────┘  │     │   │            │     │  └─────┴─────┘  │
│        │        │     │   └─────────   │     │                 │
│        │        │     │                │     │                 │
└─────────────────┘     └────────────────┘     └─────────────────┘
valid                   valid                  invalid
```
invalid cracks will be ignored.

---

### Manage pivot/edge/closure creation(basic, low level):
Remind the ownership between closure, edge and pivot is that:
Closure────►Edge────►Pivot

This low level creation api only handle 3 things:
1. create instance and add it to stretch.
2. make sure child resource is in stretch and valid.
3. make sure children's back ref to parent is correct.

We can conclude that:

```
create_pivot:
    create pivot instance
    add new pivot to stretch's pivot map
    done
```

```
create_edge:
    assert given pivot or pid is in stretch's pivot map
    create edge instance from 2 valid pivot
    update pivots' ref (in-edges and out-edges) of current edge
    add new edge to stretch's edge map
    done
```

```
create_closure:
    assert given edges are all in stretch's edge map
    create edge sequence from a bunch of edges
    create closure instance from a valid edgeSeq as exterior and possibly several edgeSeqs as holes
    update each edge's closure ref
    add new closure to stretch's closure map
```

---

### Manage pivot/edge/closure deletion:
Deletion is more complicated than creation, because deletion may make other concepts invalid and create useless garbage.
Thus, we should take care of the CORRECTNESS and GARBAGE at the SAME TIME.

This deletion api handles things:
1. delete data from stretch
2. delete the back ref of children resource to keep the validity
3. delete the necessary part of parent.

We can conclude that:

```
discard_edge: (without caring about correctness and garbage collection of closure)
    delete edge from stretch's edge map
    delete ref of edge inside its from_pivot and to_pivot(correctness)
    delete dangling pivot(clean garbage)
```

```
delete_edge:
    call discard_edge
    if edge is part of the closure's interior
        delete interior from closure(correctness)
        unset closure ref of each edge in original interior(correctness)
        call discard_edge for each edge in interior(clean garbage, optional)
    else if edge is part of the closure's exterior
        call delete_closure
```

```
delete_closure:
    unset closure ref of each edge in closure(correctness)
    call discard_edge for each edge in closure(clean garbage, optional)
    delete closure from stretch's closure map(correctness)
    done
```

```
delete_pivot:
    delete pivot from stretch's pivot map(correctness)
    call delete_edge for each edge this pivot connected to(correctness)
    done
```
---

Manage edge expansion:
expand is one of the basic operations of edge.
we can expand an edge by pivot, edge or edgeSeq.
expand will handle:
1. delete the original edge
2. create new edges
3. update the closure reference of new edges
4. the expansion of the reverse edge, if reverse edge existed

---
Manage pivot/edge/closure addition by geometry:
Based on low level pivot/edge/closure creation, addition by geometry will handle:
1. re-usage of existing pivot, based on space distance
2. attachment of new pivot to existing edges or old pivots to new edge

> NOTICE that add_edge does not handle the validity of closure, which should be done by caller.

2 distance tolerance should be considered:
- distance tolerance to pivot: if the distance between 2 pivots is less than this tolerance, they are considered
  as the same pivot.
- distance tolerance to edge: if the distance between a pivot and an edge is less than this tolerance, the pivot is
  considered on the edge, thus expand the edge.

```
add_pivot(point, dist_tol_to_pivot, dist_tol_to_edge):
    if close to existing pivot(by dist_tol_to_pivot)
    return the existing pivot
    call create_pivot
    if pivot close to existing edge(by dist_tol_to_edge)
    call edge.expand(pivot)
    return the pivot
```

```
add_edge(line, dist_tol_to_pivot, dist_tol_to_edge):
    for each point given
        call add_pivot(by dist_tol_to_pivot and dist_tol_to_edge)
        call create_edge for each pair of pivots
    for each edge created
        query pivots nearby(by dist_tol_to_edge)
        sort pivots by the value project on edge returned
        call edge.expand(pivots)
```

```
add_closure(polygon, dist_tol_to_pivot, dist_tol_to_edge):
    for each segment given by the input polygon
        call add_edge
```

## Offset Algorithm
Basically, offset is to cut the origin closure by offset edge seq into 2 or more new closures.
the closure that attaches the origin edge seq, should be deleted or union to its reverse edge closure.

Thus, the essential problem is how to cut the origin closure into 2 pieces?
```
 ┌────────────────────┐      ┌────────────────────┐
 │                    │      │                    │
 │                    │      │                    │
 │                    │      │                    │
 │                    │      │                    │
 │                    │      │                    │
 │                    │      │                    │
  \   a          ┌────┘       \ a            ┌────┘
   \  ┌──────────┤b            \─────────────┤b
    \ │          │              \            │
     \│          │               \           │
      O──────────O                O──────────O
     A            B              A            B
```

```
 ┌────────────────────┐      ┌────────────────────┐      ┌────────────────────┐
 │                    │      │                    │      │                    │
 │                    │      │                    │      │                    │
 │                    │      │                    │      │                    │
 │                    │      │a                  b│      │a               b   │
 │   a┌──────────┐b   │      ├────────────────────┤      ├───────────────┐    │
 │    │          │    │      │                    │      │               │    │
  \   │          ├────┘       \              ┌────┘       \              ├────┘
   \  │          │             \             │             \             │
    \ │          │              \            │              \            │
     \│          │               \           │               \           │
      O──────────O                O──────────O                O──────────O
     A            B              A            B              A            B
```

In any case of offset, there are 2 kinds of lines that should be considered:
1. the line after offset, namely line (a,b)
2. the line that connecting line (A,B) and (a,b), namely line (a,A) and (b,B) or path between a and A, b and B.

To calculate line (a,b), there are many strategies, we can either:
1. offset line (A,B) to get (a,b)
2. offset line (A,B) and prolong it to cut across the closure, thus point a and b must attach to the boundary of closure
3. calculate a, b with special algorithm and then form line (a,b)

To calculate connecting line, we do the following:
1. if a or b is on the boundary of closure, we don't need a connecting line for a or b
2. if not, then either:
   1. connect A and a, or B and b
   2. connect a and point on path(A,a) that is closest to a, or b in the same way.

```
  ┌────────────────────┐
  │                    │
  │                    │
  │    ┌───────┐       │
  │a   │ hole  │   b   │
  ├────┤       ├──┐    │
  │    └───────┘  │    │
   \              ├────┘
    \             │
     \            │
      \           │
       O──────────O
      A            B
```

In case of closure with holes, the only difference is that, we use holes to difference the offset line and connecting 
line above and use each segments left along with the origin boundary of closure to cut the closure into more than 
1 piece.

As conclusion, the whole offset algorithm is as follows:
```
offset(edge_seq)
    calculate offset linestring (a,b)
    calculate the connecting line of a and b and connect it to offset line above, we denote this line as L
    we calculate new L as L.intersection(closure)
    for each segment of L, we add edges in both directions
    remove the origin closure and rebuild closures according to edges
```