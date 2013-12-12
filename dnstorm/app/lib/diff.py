
def diff_prettyHtml(diffs):
    """Convert a diff array into a pretty HTML report.

    Args:
      diffs: Array of diff tuples.

    Returns:
      HTML representation.
    """
    DIFF_DELETE = -1
    DIFF_INSERT = 1
    DIFF_EQUAL = 0

    html = []
    for (op, data) in diffs:
        text = data
        if op == DIFF_INSERT:
            html.append("<ins>%s</ins>" % text)
        elif op == DIFF_DELETE:
            html.append("<del>%s</del>" % text)
        elif op == DIFF_EQUAL:
            html.append("<span>%s</span>" % text)
    return "".join(html)
