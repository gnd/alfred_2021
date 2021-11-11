FIELD_SEPARATOR = ":"
KEY_VAL_SEPARATOR = "="

# class Message:
    

def encode_msg(text):
    text = text.replace(FIELD_SEPARATOR, "") # ensure `:` is not found to adhere to protocol
    pass

def decode_msg(string_msg):
    key_val_pairs = string_msg.split(FIELD_SEPARATOR)
    key_val_arr = [x.split(KEY_VAL_SEPARATOR) for x in key_val_pairs]
    key_val_tuples = [(x[0], x[1]) for x in key_val_arr]
    key_vals = dict(key_val_tuples)
    
    # text = key_vals.get("text")
    # font_size = key_vals.get("font_size")
    # color = key_vals.get("color")
    # align = key_vals.get("align")
    return key_vals