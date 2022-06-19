from typing import Union, Optional, List
import sys
import re


class CodeLine:

    label_regex = re.compile(r'\(((\w|\.|\$|_)+)\)')
    var_regex = re.compile(r'@((\w|\.|\$|_)+)')

    def __init__(self, code_line, real_line_number):
        self.source_code_line = code_line.strip(' \n\t')
        self.target_code_line = code_line
        self.line_number = real_line_number
        self._skippable = False
        self._is_label = False

    def is_empty(self):
        return not self.target_code_line

    def is_label(self) -> bool:
        return self._is_label

    def get_label(self) -> Optional[str]:
        if self.is_label():
            match = self.label_regex.match(self.target_code_line)
            return match.group(1)

    def is_skippable(self) -> bool:
        return self.is_empty() or self.is_label()

    def clean(self):
        comment_index = self.target_code_line.find('//')
        if comment_index >= 0:
            self.target_code_line = self.target_code_line[:comment_index]
        self.target_code_line = self.target_code_line.replace(' ', '').replace('\t', '').replace('\n', '')
        self._is_label = self.label_regex.match(self.target_code_line)

    def get_variable_name(self) -> Optional[str]:
        if '@' not in self.target_code_line:
            return None
        match = self.var_regex.match(self.target_code_line)
        if not match:
            return None
        var = match.group(1)
        try:
            int(var)
        except Exception:
            return var

    def replace_variable(self, var_name: str, value: str):
        self.target_code_line = self.target_code_line.replace(f'{var_name}', value)

    def __repr__(self):
        return self.target_code_line + ' // ' + self.source_code_line


class Translator:

    def __init__(self):
        self._a_regex = re.compile('^@\d+$')

        self.dest_table = {
            'M': '001',
            'D': '010',
            'A': '100',
            'MD': '011',
            'AM': '101',
            'AD': '110',
            'AMD': '111'
        }

        self.jmp_table = {
            'JGT': '001',
            'JEQ': '010',
            'JGE': '011',
            'JLT': '100',
            'JNE': '101',
            'JLE': '110',
            'JMP': '111'
        }

        self.op_table = {
            '0': '0101010',
            '1': '0111111',
            '-1': '0111010',
            'D': '0001100',
            'A': '0110000',
            'M': '1110000',
            '!D': '0001101',
            '!A': '0110001',
            '!M': '1110001',
            '-D': '0001111',
            '-A': '0110011',
            '-M': '1110011',
            'D+1': '0011111',
            'A+1': '0110111',
            'M+1': '1110111',
            'D-1': '0001110',
            'A-1': '0110010',
            'M-1': '1110010',
            'D+A': '0000010',
            'D+M': '1000010',
            'D-A': '0010011',
            'D-M': '1010011',
            'A-D': '0000111',
            'M-D': '1000111',
            'D&A': '0000000',
            'D&M': '1000000',
            'D|A': '0010101',
            'D|M': '1010101'
        }

        dest_options = '|'.join(self.dest_table.keys())
        jmp_options = '|'.join(self.jmp_table.keys())
        op_options = '([AMD][-+]1)|(D[-+&|][AM])([AM]-D)|(0|1|-1)|([-!]?[AMD])'

        self._c_regex = re.compile('(({})=)?({})(;({}))?'.format(dest_options, op_options, jmp_options))

    def to_binary(self, num: Union[int, str]) -> str:
        num = int(num)
        return '{0:b}'.format(num)

    def translate_a_instruction(self, source_line: str) -> str:
        if not self._a_regex.match(source_line):
            raise Exception(source_line)

        number = int(source_line[1:])
        binary_number = self.to_binary(number)
        result = '0'*(16-len(binary_number)) + binary_number
        return result

    def translate_c_instruction(self, source_line: str) -> str:
        if not self._c_regex.match(source_line):
            raise Exception()

        other = source_line
        source_dest = ''
        source_op = source_dest
        source_jmp = ''

        flag = False
        if '=' in other:
            flag = True
            source_dest, other = source_line.split('=')
            source_op = other

        if ';' in other:
            flag = True
            source_op, source_jmp = other.split(';')

        if not flag:
            raise Exception()

        jmp = self.jmp_table.get(source_jmp, '000')
        dest = self.dest_table.get(source_dest, '000')
        op = self.op_table[source_op]

        return f'111{op}{dest}{jmp}'

    def translate(self, lines: List[CodeLine]) -> List[str]:
        result = []
        for line in lines:
            asm_code = line.target_code_line
            if asm_code.startswith('@'):
                try:
                    hack_line = self.translate_a_instruction(asm_code)
                except Exception:
                    raise Exception('Wrong A instruction on the {} line: {}'.format(line.line_number, line.source_code_line))
            else:
                try:
                    hack_line = self.translate_c_instruction(asm_code)
                except Exception:
                    raise Exception('Wrong C instruction on the {} line: {}'.format(line.line_number, line.source_code_line))

            result.append(hack_line)

        return result


def format_lines(lines: List[str]):
    symbol_table = {
        f'R{x}': str(x) for x in range(16)
    }
    symbol_table['SCREEN'] = '16384'
    symbol_table['KDB'] = '24576'
    symbol_table['SP'] = '0'
    symbol_table['LCL'] = '1'
    symbol_table['ARG'] = '2'
    symbol_table['THIS'] = '3'
    symbol_table['THAT'] = '4'

    code_lines: List[CodeLine] = []

    op_index = 0
    mem_index = 16

    for index, raw_line in enumerate(lines):
        line = CodeLine(raw_line, index+1)
        line.clean()
        if line.is_skippable():
            label = line.get_label()
            if label:
                symbol_table[label] = str(op_index)
        else:
            code_lines.append(line)
            op_index += 1

    for line in code_lines:
        var_name = line.get_variable_name()
        if var_name:
            value = symbol_table.get(var_name)
            if value is None:
                value = str(mem_index)
                mem_index += 1
                symbol_table[var_name] = value
            line.replace_variable(var_name, value)
    return code_lines


def main():
    argv = sys.argv
    if len(argv) < 2:
        print('No asm files')
        return

    with open(argv[1]) as f:
        str_lines = f.readlines()

    code_lines = format_lines(str_lines)
    result_lines = Translator().translate(code_lines)
    for line in result_lines:
        print(line)


if __name__ == '__main__':
    main()
