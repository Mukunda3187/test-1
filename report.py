def build_score_report(scores):
    try:
        total = sum(scores)
        average = total / len(scores)
        highest = max(scores)
    except:
        return {"error": "Could not build report"}
    return {
        "total": total,
        "average": average,
        "highest": highest,
    }
