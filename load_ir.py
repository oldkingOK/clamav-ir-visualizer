import re
from enum import Enum, auto

# 类型处理
table = {
    "[1024 x i8]": "char[1024]",
    "i64": "int64_t",
    "i32": "int32_t",
    "i8*": "char*",
    "i8": "char",
    "i1": "bool",
}

def replace_type(t):
    tmp = t
    for k, v in table.items():
        tmp = tmp.replace(k, v)
    return f"({tmp})"


class NextType(Enum):
    UNDEFINED = auto()
    JMP = auto()
    BR = auto()
    RET = auto()

class Block:
    def __init__(self, id) -> None:
        self.id = id
        self.code = []
        self.nextType = NextType.UNDEFINED
        self.nextParam = None
        """
        jmp: nextParam = block
        br:  nextParam = [condition, block1, block2]
        ret: nextParam = None
        """

class Function:
    def __init__(self, id):
        """
        globals 暂时不用读取
        asm 的话，行数不多，每个基本块的结尾有三种可能：
        1. jmp
        2. ret
        3. br
        用 python 存储每一个基本块的信息，然后生成流程图
        """
        self.id = id
        self.globals = {}
        self.locals = {}
        self.constants = {}
        self.blocks = []

    def __str__(self):
        return f"Function {self.id}:\nGlobals: IGNORE\nLocals: {len(self.locals)}\nConstants: {len(self.constants)}"

SEPERATOR = "------------------------------------------------------------------------"
lines = open("./sample/sample_ir.log").readlines()

# File readers 

class BlockReader:
    def __init__(self, lines):
        self.lines = lines

    def read(self):
        raise NotImplementedError()

class DefaultReader:
    def read(self):
        pass

class LocalsReader(BlockReader):
    def read(self) -> dict[int, str]:
        m = "XXX  ID    VALUE"
        index_id = m.find("ID")
        index_value = m.find("VALUE")
        result = {}
        for line in self.lines:
            result[line[index_id:index_id+3].strip()] = replace_type(line[index_value:])
        return result

class ConstantsReader(BlockReader):
    def read(self) -> dict[int, str]:
        m = "XXX  ID    VALUE"
        index_id = m.find("ID")
        index_value = m.find("VALUE")
        result = {}
        for line in self.lines:
            result[line[index_id:index_id+3].strip()] = line[index_value:]
        return result

ASM_TOKENS = [",", "(", ")"]

class AsmReader(BlockReader):
    def read(self, func_locals, func_constants) -> list[Block]:
        m = "BB   IDX  OPCODE              [ID /IID/MOD]  INST"
        index_bb = m.find("BB")
        index_inst = m.find("INST")

        codeblocks: dict[str, list[str]] = {}
        blocks: dict[str, Block] = {}
        "bb序号和对应的指令"
        for line in self.lines:
            id = line[index_bb:index_bb+3].strip()
            if not id in codeblocks:
                codeblocks[id] = []

            inst = line[index_inst:]
            [inst := inst.replace(t, f" {t} ") for t in ASM_TOKENS]
            tokens = inst.split(" ")
            for i in range(len(tokens)):
                if tokens[i] in func_locals:
                    tokens[i] = f"{func_locals[tokens[i]]}v_{tokens[i]}"
                elif tokens[i] in func_constants:
                    tokens[i] = f"{func_constants[tokens[i]]}"
            codeblocks[id].append(" ".join([t for t in tokens if t != ""]))

            # 最后一行处理 ret jmp br 逻辑
            if not tokens[0] in ["jmp", "br", "ret"]:
                continue

            # start process block
            block = Block(id)
            block.code = codeblocks[id]

            match tokens[0]:
                case 'br':
                    block.nextType = NextType.BR
                    block.nextParam = [tokens[1], tokens[3], tokens[5]]
                    pass
                case 'jmp':
                    block.nextType = NextType.JMP
                    block.nextParam = tokens[1]
                    pass
                case 'ret':
                    block.nextType = NextType.RET
                    block.nextParam = None
                    pass

            blocks[id] = block
        
        return blocks


# get blocks
blocks = []
tmp_block = []
for line in lines:
    if SEPERATOR in line:
        blocks.append(tmp_block)
        tmp_block = []
    else:
        tmp_block.append(line[:-1])

funcs = []
# get functions
for i in range(len(blocks)):
    if any(["Function id" in line for line in blocks[i]]):
        func = Function(int(re.findall(r"\d+", blocks[i][1])[0]))
        func.locals = LocalsReader(blocks[i+3]).read()
        func.constants = ConstantsReader(blocks[i+5]).read()
        func.blocks = AsmReader(blocks[i+8]).read(func.locals, func.constants)
        funcs.append(func)