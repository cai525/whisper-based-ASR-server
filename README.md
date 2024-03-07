# whisper-based ASR server
该项目旨在实现一个用于语音翻译(ASR)服务器;
- ASR 识别基于 [Whisper](https://github.com/openai/whisper)
- 服务器后端基于 
    - nginx: 用于提供静态网页的https服务 
    - tornado: 一个Python web框架和异步网络库. 通过使用非阻塞网络I/O, Tornado 可以支持上万级的连接，处理 长连接、WebSockets、和其他需要与每个用户保持长久连接的应用.
- 前端代码使用 html+css+js 编写的网页;