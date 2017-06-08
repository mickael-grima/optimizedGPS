
def get_percentage(part, total, trunc=2):
    return int(float(part) / total * (10 ** (trunc + 2))) / float((10 ** trunc))
