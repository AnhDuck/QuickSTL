import adsk.core


def find_input(inputs: adsk.core.CommandInputs, input_id: str):
    if not inputs or not input_id:
        return None
    try:
        found = inputs.itemById(input_id)
        if found:
            return found
    except Exception:
        pass
    stack = [inputs]
    try:
        while stack:
            coll = stack.pop()
            for i in range(coll.count):
                item = coll.item(i)
                try:
                    if getattr(item, "id", "") == input_id:
                        return item
                except Exception:
                    pass
                if isinstance(item, adsk.core.GroupCommandInput):
                    stack.append(item.children)
    except Exception:
        pass
    return None
