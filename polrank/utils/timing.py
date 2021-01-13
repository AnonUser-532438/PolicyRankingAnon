def sec_to_str(s, padh=2):
    s = int(s)

    h = int(s / 3600)
    s = s % 3600

    m = int(s / 60)
    s = s % 60

    return "{0:0{3}d}:{1:02d}.{2:02d}".format(h, m, s, padh)
