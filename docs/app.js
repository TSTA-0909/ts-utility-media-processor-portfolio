const SAMPLE_RESULTS = {"original":{"bytes":1089031,"width":2400,"height":1680},"variants":[{"id":"share","name":"社内提出・共有用","width":600,"height":420,"quality":68,"bytes":18019,"filename":"after-share.jpg","preset_key":"社内提出・共有用（推奨・最軽量）","diagnosis":"総合判定：一般的な社内資料・帳票の印刷なら実用範囲の目安です。\n文字　★★★★☆\n図面・罫線　★★★★☆\n写真　★★★☆☆\n最軽量画像設定は社内資料への貼付印刷を想定した実用優先の設定です。 画像は600×420px基準・JPEG品質68で処理しています。 削減率が非常に高いため、背景や細かな写真部分には圧縮感が出る場合があります。\n※設定・解像度・圧縮率から算出する目安です。プリンター・用紙・原稿品質によって実際の印刷結果は変わります。","reduction":98.3},{"id":"email","name":"メール添付用","width":800,"height":560,"quality":75,"bytes":29473,"filename":"after-email.jpg","preset_key":"メール添付用（軽量）","diagnosis":"総合判定：一般的な社内資料・帳票の印刷なら実用範囲の目安です。\n文字　★★★★☆\n図面・罫線　★★★★☆\n写真　★★★☆☆\n画像は800×560px基準・JPEG品質75で処理しています。 削減率が非常に高いため、背景や細かな写真部分には圧縮感が出る場合があります。\n※設定・解像度・圧縮率から算出する目安です。プリンター・用紙・原稿品質によって実際の印刷結果は変わります。","reduction":97.3},{"id":"report","name":"社内報告書用","width":1000,"height":700,"quality":82,"bytes":48983,"filename":"after-report.jpg","preset_key":"社内報告書用（標準）","diagnosis":"総合判定：一般的な社内資料・帳票の印刷なら実用範囲の目安です。\n文字　★★★★☆\n図面・罫線　★★★★☆\n写真　★★★★☆\n画像は1000×700px基準・JPEG品質82で処理しています。 削減率が非常に高いため、背景や細かな写真部分には圧縮感が出る場合があります。\n※設定・解像度・圧縮率から算出する目安です。プリンター・用紙・原稿品質によって実際の印刷結果は変わります。","reduction":95.5},{"id":"screen","name":"画面確認用","width":1600,"height":1120,"quality":88,"bytes":149025,"filename":"after-screen.jpg","preset_key":"画面確認用（高画質）","diagnosis":"総合判定：高品質印刷まで期待できる設定です。\n文字　★★★★★\n図面・罫線　★★★★☆\n写真　★★★★☆\n画像は1600×1120px基準・JPEG品質88で処理しています。\n※設定・解像度・圧縮率から算出する目安です。プリンター・用紙・原稿品質によって実際の印刷結果は変わります。","reduction":86.3}],"method":"User-provided Python image_engine.resize_image, processing_presets.IMAGE_PRESETS","sample":"合成画像（架空の風景）","display_note":"新しい元画像は粒状ノイズを意図的に減らし、細い線や小さな文字を含めた架空風景。比較画像は元画像を基に実エンジンで生成。"};
(()=>{
  const $=id=>document.getElementById(id);
  const variants=Object.fromEntries(SAMPLE_RESULTS.variants.map(v=>[v.id,v]));
  const fmt=b=>(b/1024/1024>=1?(b/1048576).toFixed(2)+' MB':Math.max(1,Math.round(b/1024))+' KB');
  const guideSteps=[
    {title:'① 用途を選んでみよう',desc:'「社内提出用」「メール添付用」などを押してみて。容量がどう変わるか見比べよう。',element:'targetPresets'},
    {title:'② 実際の処理前後を比べよう',desc:'下のスライダーを左右に動かして、元画像とPythonの処理結果を比較しよう。',element:'targetComparison'},
    {title:'③ 画像の自動診断を見てみよう',desc:'選んだ用途によって解像度・JPEG品質が変わり、実際のPythonの判定結果も切り替わります。',element:'targetDiagnosis'},
    {title:'④ PDFの自動判断も試してみよう',desc:'架空のPDF特徴データを切り替えると、文字・図面・写真の数からおすすめ設定がどう変わるかを確認できます。',element:'targetPdfRules'},
    {title:'⑤ 本物の操作画面を確認しよう',desc:'ここが実際に作られたPython/Tkinter製のWindowsアプリ。用途に合わせて使いやすくする工夫も確認できます。',element:'native'}
  ];
  let guideStep=0;
  let guideEnabled=true;
  const highlight=()=>{
    document.querySelectorAll('.guide-highlight').forEach(n=>n.classList.remove('guide-highlight'));
    if(!guideEnabled)return;
    const data=guideSteps[guideStep];
    const target=$(data.element);
    if(target)target.classList.add('guide-highlight');
    $('guideTitle').textContent=data.title;
    $('guideText').textContent=data.desc;
    $('guideCounter').textContent=`${guideStep+1} / ${guideSteps.length}`;
    $('guideNext').textContent=guideStep===guideSteps.length-1?'体験を続ける ↻':'次へ進む →';
  };
  function setGuideEnabled(on){
    guideEnabled=Boolean(on);
    $('guide').hidden=!guideEnabled;
    $('guideToggle').textContent=guideEnabled?'操作ガイド：ON':'操作ガイド：OFF';
    $('guideToggle').setAttribute('aria-pressed',String(guideEnabled));
    highlight();
  }
  function gotoStep(n){
    guideStep=(n+guideSteps.length)%guideSteps.length;
    highlight();
    $(guideSteps[guideStep].element)?.scrollIntoView({behavior:'smooth',block:'center'});
  }
  function updateComparison(pct){
    const value=Number(pct);
    $('comparison').style.setProperty('--split',value+'%');
    $('rangeValue').textContent=value+'%';
  }
  function updateDiagnosis(data){
    $('diagnosticPreset').textContent=`用途：${data.name}（自動設定）`;
    $('diagnosticDimensions').textContent=`${data.width} × ${data.height} px`;
    $('diagnosticQuality').textContent=`${data.quality} / 100`;
    const lines=data.diagnosis.trim().split('\n');
    $('diagnosticVerdict').textContent=lines[0];
    const labels=['文字','図面・罫線','写真'];
    $('diagnosticScores').replaceChildren();
    for (const line of lines){
      for (const label of labels){
        if(!line.startsWith(label)) continue;
        const row=document.createElement('div');row.className='score-row';
        const title=document.createElement('span');title.textContent=label;
        const stars=document.createElement('span');stars.textContent=line.slice(label.length).trim();
        row.append(title,stars);$('diagnosticScores').appendChild(row);
      }
    }
    $('diagnosticReasons').textContent=lines.filter(line=>!line.startsWith('総合判定：')&&!labels.some(label=>line.startsWith(label))).join(' ');
  }
  // These metadata samples are fictional. The same threshold order as pdf_optimization_diagnosis.py is used.
  const pdfCases={
    photos:{name:'写真が多い現場報告書',images:3.5,drawings:2,chars:160},
    drawing:{name:'境界線・図形が多い図面',images:0.5,drawings:24,chars:920},
    dense:{name:'細字・極めて高密度な図面',images:1,drawings:110,chars:2800},
    text:{name:'テキスト中心の文書',images:0,drawings:4,chars:510},
    scan:{name:'画像としてスキャンされた資料',images:1.5,drawings:0,chars:0}
  };
  function classifyPdf(f){
    const isDense=f.drawings>=90||f.chars>=2600;
    const isDrawing=f.drawings>=12||f.chars>=650;
    if(isDense) return {category:'極細字・高密度図面主体',preset:'細字・求積図用（高精細）',reason:'小さな文字や図形が非常に密集しています。標準でも軽量化できますが、拡大確認や数値判読を優先して高精細設定へ引き上げます。',drawing:true};
    if(isDrawing) return {category:'公図・求積図・細線図面主体',preset:'図面・公図用（標準）',reason:'細い斜線・境界線・小さな数字が多い図面です。最軽量では線がギザつく可能性があるため標準設定をおすすめします。',drawing:true};
    if(f.chars<20&&f.images>=1) return {category:'スキャン資料・画像図面主体',preset:'図面・公図用（標準）',reason:'文字情報を持たない画像主体のPDFです。公図・求積図などの細線を守るため最軽量ではなく標準設定をおすすめします。',drawing:true};
    if(f.images>=2.5&&f.chars<500&&f.drawings<10) return {category:'現場写真報告書',preset:'現場写真報告書用（推奨・最軽量）',reason:'1ページあたりの写真が多く、文字・図形が少ない写真報告書なので最軽量設定をおすすめします。',drawing:false};
    if(f.images>=1) return {category:'写真・図面混在資料',preset:'図面・公図用（標準）',reason:'写真だけでなく線・文字も含むため最軽量より標準設定をおすすめします。',drawing:true};
    return {category:'文字・ベクター主体',preset:'社内共有用（軽量）',reason:'文字・ベクター中心なので、軽量設定でも見た目が変わりにくい構成です。',drawing:false};
  }
  function updatePdfExample(){
    const s=pdfCases[$('pdfScenario').value]||pdfCases.photos;
    const result=classifyPdf(s);
    $('pdfFeatures').replaceChildren();
    for(const label of [`1ページあたりの写真：${s.images}点`,`図形：${s.drawings}件`,`文字：${s.chars}文字`]){
      const part=document.createElement('span');part.textContent=label;$('pdfFeatures').appendChild(part);
    }
    $('pdfCategory').textContent=result.category;
    $('pdfPreset').textContent=result.preset;
    $('pdfEnhancement').textContent=result.drawing?'図面・文字優先':'境界線・テープ優先（おすすめ）';
    $('pdfReason').textContent=result.reason;
  }
  let current='share';
  function choosePreset(id){
    const data=variants[id];if(!data)return;
    current=id;
    $('afterImage').src='assets/'+data.filename;
    $('afterImage').alt=`Pythonで生成した${data.name}の比較画像`;
    $('originalSize').textContent=fmt(SAMPLE_RESULTS.original.bytes);
    $('outputSize').textContent=fmt(data.bytes);
    $('reduction').textContent=((1-data.bytes/SAMPLE_RESULTS.original.bytes)*100).toFixed(1)+'%';
    $('resolution').textContent=`解像度：${SAMPLE_RESULTS.original.width}×${SAMPLE_RESULTS.original.height} → ${data.width}×${data.height} px`;
    updateDiagnosis(data);
    document.querySelectorAll('[data-preset]').forEach(btn=>{let selected=btn.dataset.preset===id;btn.classList.toggle('selected',selected);btn.setAttribute('aria-pressed',String(selected));});
    if(guideEnabled&&guideStep===0)gotoStep(1);
  }
  document.querySelectorAll('[data-preset]').forEach(btn=>btn.addEventListener('click',()=>choosePreset(btn.dataset.preset)));
  $('compareRange').addEventListener('input',e=>{updateComparison(e.target.value);if(guideEnabled&&guideStep===1)highlight();});
  $('openOutput').addEventListener('click',()=>window.open('assets/'+variants[current].filename,'_blank','noopener'));
  $('openOriginal').addEventListener('click',()=>window.open('assets/before.jpg','_blank','noopener'));
  $('zoomDetail').addEventListener('change',e=>$('comparison').classList.toggle('is-zoomed',e.target.checked));
  $('pdfScenario').addEventListener('change',updatePdfExample);
  $('guideToggle').addEventListener('click',()=>setGuideEnabled(!guideEnabled));
  $('guideClose').addEventListener('click',()=>setGuideEnabled(false));
  $('guideNext').addEventListener('click',()=>gotoStep(guideStep+1));
  updateComparison(52);
  // Avoid automatically progressing from the first step merely by loading sample data.
  const data=variants.share;
  $('originalSize').textContent=fmt(SAMPLE_RESULTS.original.bytes);
  $('outputSize').textContent=fmt(data.bytes);
  $('reduction').textContent=((1-data.bytes/SAMPLE_RESULTS.original.bytes)*100).toFixed(1)+'%';
  $('resolution').textContent=`解像度：2400×1680 → ${data.width}×${data.height} px`;
  updateDiagnosis(data);
  updatePdfExample();
  highlight();
})();
