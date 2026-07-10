def run(payload):
    endpoint = payload.get("endpoint", "")
    method = payload.get("method", "")
    return {
        "endpoint": endpoint,
        "method": method,
        "test_points": [
            "必填参数校验",
            "参数类型和边界校验",
            "鉴权和权限校验",
            "业务状态流转校验",
            "错误码和错误信息校验",
        ],
    }
