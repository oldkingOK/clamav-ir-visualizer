from PyMermaid.mermaid import flowchart as f
from load_ir import *

f.set_layout(f.layout_topToBottom)
def render(func, output):
    nodes = {}
    for id, block in func.blocks.items():
        codes = '\n'.join(block.code)
        nodes[id] = f.add_node(f'<div style="text-align: center;"><b>bb.{id}</b></div>{codes}')
        f._internal.code.append(f"style {id} text-align:left")

    for id, block in func.blocks.items():
        match block.nextType:
            case NextType.BR:
                f.link(nodes[id], nodes[block.nextParam[1][3:]], f.add_arrow(type=f.arrowType_normalArrow, text=block.nextParam[0]))
                f.link(nodes[id], nodes[block.nextParam[2][3:]], f.add_arrow(type=f.arrowType_normalArrow, text=f"!{block.nextParam[0]}"))
            case NextType.JMP:
                f.link(nodes[id], nodes[block.nextParam[3:]], f.add_arrow(type=f.arrowType_normalArrow))
            case NextType.RET:
                pass    

    open(output, "w").write(f.evaluate())

if __name__ == "__main__":
    for i in range(len(funcs)):
        render(funcs[i], f"func{i}.html")