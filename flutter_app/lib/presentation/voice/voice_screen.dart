import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_tts/flutter_tts.dart';
import '../../core/theme/app_theme.dart';
import '../../core/network/dio_client.dart';
import '../../core/constants.dart';

// 음성 화면 상태
enum _VoiceState { idle, listening, processing, speaking }

// 대화 메시지
class _Msg {
  final String text;
  final bool isUser;
  _Msg(this.text, this.isUser);
}

final _msgsProvider = StateProvider<List<_Msg>>((ref) => []);

class VoiceScreen extends ConsumerStatefulWidget {
  const VoiceScreen({super.key});

  @override
  ConsumerState<VoiceScreen> createState() => _VoiceScreenState();
}

class _VoiceScreenState extends ConsumerState<VoiceScreen>
    with TickerProviderStateMixin {
  final _speech = stt.SpeechToText();
  final _tts    = FlutterTts();
  final _scroll = ScrollController();

  _VoiceState _state = _VoiceState.idle;
  String _partial = '';
  bool _ready = false;

  late AnimationController _pulseCtrl;
  late Animation<double>   _pulseAnim;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 900))
      ..repeat(reverse: true);
    _pulseAnim = Tween(begin: 1.0, end: 1.45).animate(
        CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut));
    _initSpeech();
    _initTts();
  }

  Future<void> _initSpeech() async {
    _ready = await _speech.initialize(
      onStatus: (s) {
        if ((s == 'done' || s == 'notListening') &&
            _state == _VoiceState.listening) {
          _stopListen();
        }
      },
    );
    if (mounted) setState(() {});
  }

  Future<void> _initTts() async {
    await _tts.setLanguage('ko-KR');
    await _tts.setSpeechRate(0.48);
    await _tts.setVolume(1.0);
    await _tts.setPitch(1.0);
    _tts.setCompletionHandler(() {
      if (mounted) setState(() => _state = _VoiceState.idle);
    });
  }

  Future<void> _tap() async {
    if (_state == _VoiceState.idle)      { _startListen(); return; }
    if (_state == _VoiceState.listening) { _stopListen();  return; }
    if (_state == _VoiceState.speaking)  { await _tts.stop(); setState(() => _state = _VoiceState.idle); }
  }

  Future<void> _startListen() async {
    if (!_ready) {
      _addMsg('마이크 권한이 필요합니다. 설정에서 허용해 주세요.', false);
      return;
    }
    await _tts.stop();
    setState(() { _state = _VoiceState.listening; _partial = ''; });
    await _speech.listen(
      onResult: (r) {
        setState(() => _partial = r.recognizedWords);
        if (r.finalResult && r.recognizedWords.isNotEmpty) _stopListen();
      },
      localeId: 'ko_KR',
      listenMode: stt.ListenMode.confirmation,
    );
  }

  Future<void> _stopListen() async {
    await _speech.stop();
    final text = _partial.trim();
    setState(() { _state = _VoiceState.processing; _partial = ''; });
    if (text.isEmpty) { setState(() => _state = _VoiceState.idle); return; }
    _addMsg(text, true);
    await _query(text);
  }

  void _addMsg(String text, bool isUser) {
    ref.read(_msgsProvider.notifier).update((l) => [...l, _Msg(text, isUser)]);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
      }
    });
  }

  Future<void> _query(String text) async {
    try {
      final dio = ref.read(dioProvider);
      final res = await dio.post(ApiPath.voiceQuery, data: {'query': text});
      final reply = res.data['response'] as String? ?? '응답을 받지 못했습니다.';
      _addMsg(reply, false);
      setState(() => _state = _VoiceState.speaking);
      await _tts.speak(reply);
    } catch (_) {
      _addMsg('죄송합니다, 지금은 답변하기 어렵습니다. 잠시 후 다시 시도해 주세요.', false);
      setState(() => _state = _VoiceState.idle);
    }
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    _scroll.dispose();
    _speech.stop();
    _tts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final msgs = ref.watch(_msgsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            width: 8, height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _state == _VoiceState.idle
                  ? AppColors.textHint
                  : AppColors.neonGreen,
              boxShadow: _state != _VoiceState.idle ? [
                BoxShadow(color: AppColors.neonGreen.withOpacity(0.6),
                    blurRadius: 6, spreadRadius: 1),
              ] : null,
            ),
          ),
          const SizedBox(width: 8),
          const Text('자비스 AI 어시스턴트'),
        ]),
        actions: [
          if (msgs.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.clear_all),
              onPressed: () =>
                  ref.read(_msgsProvider.notifier).state = [],
            ),
        ],
      ),
      body: Column(children: [
        // ── 대화 영역 ──────────────────────────────
        Expanded(
          child: msgs.isEmpty
              ? _Welcome(ready: _ready)
              : ListView.builder(
                  controller: _scroll,
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
                  itemCount: msgs.length,
                  itemBuilder: (_, i) => _Bubble(msgs[i]),
                ),
        ),

        // ── 실시간 인식 텍스트 ──────────────────────
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 200),
          child: _partial.isNotEmpty
              ? Container(
                  key: const ValueKey('partial'),
                  margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppColors.neonGreen.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppColors.neonGreen.withOpacity(0.3)),
                  ),
                  child: Text(_partial,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                          color: AppColors.neonGreen, fontSize: 14)),
                )
              : const SizedBox(key: ValueKey('empty'), height: 0),
        ),

        // ── 상태 텍스트 ────────────────────────────
        Padding(
          padding: const EdgeInsets.only(top: 6, bottom: 4),
          child: Text(_label, style: TextStyle(color: _labelColor, fontSize: 12)),
        ),

        // ── 마이크 버튼 ────────────────────────────
        Padding(
          padding: const EdgeInsets.only(bottom: 44, top: 8),
          child: GestureDetector(
            onTap: _state == _VoiceState.processing ? null : _tap,
            child: SizedBox(
              width: 110,
              height: 110,
              child: Stack(alignment: Alignment.center, children: [
                // 펄스 링 2겹
                if (_state == _VoiceState.listening ||
                    _state == _VoiceState.speaking)
                  ...[1.0, 1.35].map((factor) => AnimatedBuilder(
                    animation: _pulseAnim,
                    builder: (_, __) => Transform.scale(
                      scale: _pulseAnim.value * factor,
                      child: Container(
                        width: 82,
                        height: 82,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: _btnColor
                                .withOpacity(factor == 1.0 ? 0.55 : 0.2),
                            width: 1.8,
                          ),
                        ),
                      ),
                    ),
                  )),

                // 메인 버튼
                Container(
                  width: 74,
                  height: 74,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _btnColor.withOpacity(0.13),
                    border: Border.all(color: _btnColor, width: 2),
                    boxShadow: _state != _VoiceState.idle ? [
                      BoxShadow(
                          color: _btnColor.withOpacity(0.35),
                          blurRadius: 16,
                          spreadRadius: 2),
                    ] : null,
                  ),
                  child: _state == _VoiceState.processing
                      ? const Padding(
                          padding: EdgeInsets.all(22),
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: AppColors.neonBlue))
                      : Icon(_icon, color: _btnColor, size: 32),
                ),
              ]),
            ),
          ),
        ),
      ]),
    );
  }

  String get _label => switch (_state) {
    _VoiceState.idle       => _ready ? '버튼을 눌러 말씀하세요' : '마이크 초기화 중...',
    _VoiceState.listening  => '듣고 있습니다 — 말씀을 마치시면 자동 전송됩니다',
    _VoiceState.processing => 'AI가 분석 중입니다...',
    _VoiceState.speaking   => '자비스가 답변 중입니다 — 버튼을 누르면 중단',
  };

  Color get _labelColor => switch (_state) {
    _VoiceState.idle       => AppColors.textHint,
    _VoiceState.listening  => AppColors.neonGreen,
    _VoiceState.processing => AppColors.neonBlue,
    _VoiceState.speaking   => AppColors.neonBlue,
  };

  Color get _btnColor => switch (_state) {
    _VoiceState.idle       => AppColors.textSecondary,
    _VoiceState.listening  => AppColors.neonGreen,
    _VoiceState.processing => AppColors.neonBlue,
    _VoiceState.speaking   => AppColors.neonBlue,
  };

  IconData get _icon => switch (_state) {
    _VoiceState.idle      => Icons.mic_none_outlined,
    _VoiceState.listening => Icons.mic,
    _VoiceState.processing => Icons.hourglass_top,
    _VoiceState.speaking  => Icons.volume_up_outlined,
  };
}

// ── 말풍선 ────────────────────────────────────────────────────────
class _Bubble extends StatelessWidget {
  const _Bubble(this.msg);
  final _Msg msg;

  @override
  Widget build(BuildContext context) {
    final isUser = msg.isUser;
    return Padding(
      padding: EdgeInsets.only(
        bottom: 10,
        left:  isUser ? 48 : 0,
        right: isUser ? 0  : 48,
      ),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!isUser) ...[
            Container(
              width: 30, height: 30,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.neonBlue.withOpacity(0.15),
                border: Border.all(
                    color: AppColors.neonBlue.withOpacity(0.4)),
              ),
              child: const Icon(Icons.smart_toy_outlined,
                  color: AppColors.neonBlue, size: 16),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isUser
                    ? AppColors.neonGreen.withOpacity(0.12)
                    : AppColors.bgCard,
                borderRadius: BorderRadius.only(
                  topLeft:     const Radius.circular(16),
                  topRight:    const Radius.circular(16),
                  bottomLeft:  Radius.circular(isUser ? 16 : 4),
                  bottomRight: Radius.circular(isUser ? 4  : 16),
                ),
                border: Border.all(
                  color: isUser
                      ? AppColors.neonGreen.withOpacity(0.3)
                      : AppColors.border,
                ),
              ),
              child: Text(msg.text,
                  style: TextStyle(
                      color: isUser
                          ? AppColors.neonGreen
                          : AppColors.textPrimary,
                      fontSize: 14)),
            ),
          ),
        ],
      ),
    );
  }
}

// ── 환영 화면 ─────────────────────────────────────────────────────
class _Welcome extends StatelessWidget {
  const _Welcome({required this.ready});
  final bool ready;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      Container(
        width: 80, height: 80,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: AppColors.neonBlue.withOpacity(0.1),
          border: Border.all(
              color: AppColors.neonBlue.withOpacity(0.4), width: 2),
        ),
        child: const Icon(Icons.smart_toy_outlined,
            color: AppColors.neonBlue, size: 40),
      ),
      const SizedBox(height: 20),
      const Text('안녕하세요, 자비스입니다.',
          style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 18,
              fontWeight: FontWeight.bold)),
      const SizedBox(height: 10),
      const Text('주식 분석, 종목 추천, 지표 설명 등\n무엇이든 말씀해 주세요.',
          textAlign: TextAlign.center,
          style: TextStyle(
              color: AppColors.textSecondary, fontSize: 13)),
      const SizedBox(height: 24),
      _HintChips(),
    ]),
  );
}

class _HintChips extends StatelessWidget {
  static const _hints = [
    '오늘 추천 종목은?',
    '삼성전자 RSI 어때?',
    'MACD가 뭐야?',
    '지금 매수해도 될까?',
  ];

  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 8,
    runSpacing: 8,
    alignment: WrapAlignment.center,
    children: _hints.map((h) => Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.bgCard,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Text(h,
          style: const TextStyle(
              color: AppColors.textHint, fontSize: 12)),
    )).toList(),
  );
}
