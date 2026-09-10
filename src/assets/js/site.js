// 移动端导航开合 + 内部预览用的皮肤切换（?skin=earth / dark）
(function () {
  var btn = document.querySelector('.navtoggle');
  var nav = document.getElementById('nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.setAttribute('aria-label', open ? '收起导航' : '展开导航');
    });
  }

  // 配色切换：页脚按钮或 ?skin= 参数，选择记在本机
  var KEY = 'hbjk-skin';
  var VALID = { blue: 1, earth: 1, dark: 1 };
  var btns = document.querySelectorAll('[data-skin-set]');

  function applySkin(name) {
    if (!VALID[name]) name = 'blue';
    document.documentElement.setAttribute('data-skin', name);
    try { localStorage.setItem(KEY, name); } catch (e) {}
    for (var i = 0; i < btns.length; i++) {
      btns[i].setAttribute('aria-pressed',
        btns[i].getAttribute('data-skin-set') === name ? 'true' : 'false');
    }
  }

  for (var i = 0; i < btns.length; i++) {
    btns[i].addEventListener('click', function () {
      applySkin(this.getAttribute('data-skin-set'));
    });
  }

  var initial = 'blue';
  try {
    var q = new URLSearchParams(location.search).get('skin');
    initial = q || localStorage.getItem(KEY) || 'blue';
  } catch (e) {}
  applySkin(initial);

  // 埋点：记录哪个页面带来了联系动作。_hmt 未加载时静默跳过。
  function track(action, label) {
    try {
      if (window._hmt) window._hmt.push(['_trackEvent', '联系', action, label || location.pathname]);
    } catch (e) {}
  }
  document.querySelectorAll('a[href^="tel:"]').forEach(function (a) {
    a.addEventListener('click', function () { track('点击电话', location.pathname); });
  });
  document.querySelectorAll('a[href^="mailto:"]').forEach(function (a) {
    a.addEventListener('click', function () { track('点击邮箱', location.pathname); });
  });
  var inquiry = document.querySelector('.form');
  if (inquiry) inquiry.addEventListener('submit', function () { track('提交表单', location.pathname); });
  document.querySelectorAll('.maps__b').forEach(function (b) {
    b.addEventListener('click', function () { track('地图导航', b.textContent.trim()); });
  });

  // 复制地址
  document.querySelectorAll('.maps__copy').forEach(function (b) {
    b.addEventListener('click', function () {
      var txt = b.getAttribute('data-copy');
      var done = function () {
        var old = b.textContent;
        b.textContent = '已复制';
        b.classList.add('is-done');
        setTimeout(function () { b.textContent = old; b.classList.remove('is-done'); }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).then(done, function () {});
      } else {
        var ta = document.createElement('textarea');
        ta.value = txt; ta.style.position = 'fixed'; ta.style.left = '-9999px';
        document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); done(); } catch (e) {}
        ta.remove();
      }
    });
  });

  // 表单提交成功后的提示
  if (location.search.indexOf('ok=1') > -1) {
    var f = document.querySelector('.form');
    if (f) {
      var tip = document.createElement('p');
      tip.className = 'form__hint';
      tip.style.color = 'var(--c-head)';
      tip.textContent = '已收到，我们会尽快与您联系。';
      f.prepend(tip);
    }
  }
})();
