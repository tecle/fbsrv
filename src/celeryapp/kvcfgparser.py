# coding:utf-8
import logging


class ConfigItem(object):
    _null = object()

    def __repr__(self):
        out = []
        for attr in dir(self):
            if not attr.startswith('__'):
                attr_val = getattr(self, attr)
                if isinstance(attr_val, ConfigItem):
                    out += ['{}.{}'.format(attr, line) for line in repr(attr_val).split('\n')]
                else:
                    out.append('{}={}'.format(attr, attr_val))
        return '\n'.join(out)

    def get(self, key, default=_null):
        val = getattr(self, key, default)
        if val == self._null:
            raise ValueError('attribute %s not exist.' % key)
        return val


class KeyValueConfigParser(object):
    def parse(self, cfg_file_path):
        with open(cfg_file_path, "rb") as f:
            cfg_ctnt = f.read()
        if not cfg_ctnt:
            logging.error("Read file failed.")
            return False
        kv_map = {}
        for line in cfg_ctnt.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pos = line.find("=")
            if pos < 0:
                continue
            key = line[0:pos].strip()
            val = self._process_val(line[pos + 1:])
            kv_map[key] = val
            self.set_conf(key, val)
        return True

    def set_conf(self, key, val):
        logging.debug('Set conf: %48s -> %s', key, val)
        sections = key.split('.')
        inst = self
        for sec_name in sections[:-1]:
            if not hasattr(inst, sec_name):
                setattr(inst, sec_name, ConfigItem())
            inst = getattr(inst, sec_name)
        setattr(inst, sections[-1], val)

    def _process_val(self, value):
        stack = []
        ret = []
        for ch in value.strip():
            if stack and stack[-1] == '\\':
                ret.append(ch)
                stack.pop(-1)
            elif ch == '\\':
                stack.append(ch)
            elif ch == '"':
                if stack and stack[-1] == '"':
                    return ''.join(ret)
                if not stack:
                    if ret:
                        raise ValueError('invalid value: %s' % value.strip())
                    stack.append('"')
            elif ch == '#':
                if stack and stack[-1] == '"':
                    ret.append(ch)
                else:
                    return ''.join(ret).strip()
            else:
                ret.append(ch)
        return ''.join(ret).strip()

    def __repr__(self):
        out = []
        for attr in dir(self):
            if not attr.startswith('__'):
                attr_val = getattr(self, attr)
                if isinstance(attr_val, ConfigItem):
                    out += ['{}.{}'.format(attr, line) for line in repr(attr_val).split('\n')]
        return '\n'.join(out)
