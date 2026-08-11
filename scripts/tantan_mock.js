/*
 * 探探日志上报伪装成功响应脚本
 * 注入 code: 0 让探探 SDK 判定日志上报成功，主动平息 1秒/5秒 定时器连发
 */
$done({
  status: "HTTP/1.1 200 OK",
  headers: { "Content-Type": "application/json; charset=utf-8" },
  body: '{"code":0,"msg":"success","data":{}}'
});
