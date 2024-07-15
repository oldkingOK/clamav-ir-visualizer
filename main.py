from PyMermaid.mermaid import flowchart as f
from ir_loader import *
from sys import argv

f.set_layout(f.layout_topToBottom)
template = open("template.html").read()

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

    open(output, "w").write(template
                            .replace("{{ title }}", output)
                            .replace("{{ content }}", 
                                    f.evaluate(clear=True)
                                        .replace("```mermaid\n", "")
                                        .replace("\n```", "")))

if __name__ == "__main__":
    funcs = load_ir(argv[1] if len(argv) > 1 else "./sample/sample_ir.log")
    for i in range(len(funcs)):
        render(funcs[i], f"func{i}.html")