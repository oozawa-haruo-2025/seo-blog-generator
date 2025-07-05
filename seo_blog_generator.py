import streamlit as st
import anthropic
import time
import re
from typing import Optional, Dict, Any

# ページ設定
st.set_page_config(
    page_title="SEO記事生成ツール",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        font-size: 2.5em;
        margin-bottom: 0.5em;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2em;
        margin-bottom: 2em;
    }
    .input-section {
        background-color: #f8f9fa;
        padding: 1.5em;
        border-radius: 10px;
        margin-bottom: 2em;
    }
    .output-section {
        background-color: #ffffff;
        padding: 1.5em;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    .step-guide {
        background-color: #e3f2fd;
        padding: 1em;
        border-radius: 5px;
        margin-bottom: 1em;
        border-left: 4px solid #2196f3;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1em;
        border-radius: 5px;
        margin: 1em 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1em;
        border-radius: 5px;
        margin: 1em 0;
    }
</style>
""", unsafe_allow_html=True)

class SEOBlogGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        if api_key:
            try:
                self.client = anthropic.Anthropic(api_key=api_key)
            except Exception as e:
                st.error(f"API初期化エラー: {str(e)}")
    
    def validate_inputs(self, keyword: str, genre: str, target_audience: str) -> Dict[str, Any]:
        """入力値の検証"""
        errors = []
        
        if not keyword or len(keyword.strip()) < 2:
            errors.append("メインキーワードは2文字以上で入力してください")
        
        if not genre:
            errors.append("記事のジャンルを選択してください")
        
        if not target_audience:
            errors.append("想定読者層を選択してください")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    def generate_titles(self, keyword: str, genre: str = "", target_audience: str = "") -> Optional[str]:
        """タイトル候補のみを生成"""
        if not self.client:
            return None
        
        genre_text = f"- ジャンル: {genre}\n" if genre else ""
        audience_text = f"- 想定読者: {target_audience}\n" if target_audience else ""
        
        prompt = f"""
あなたはSEO対策に精通したプロのライターです。以下のキーワードに基づいて、SEO最適化されたタイトル候補を5つ作成してください。

## 条件
- メインキーワード: {keyword}
{genre_text}{audience_text}

## タイトル作成要件
- SEOを意識したキーワード配置
- クリックされやすい魅力的なタイトル
- 検索意図に合致した内容
- 文字数は28-32文字程度を推奨
- 数字や年号、記号の活用
- 図解、画像、動画等の視覚要素は含めない（テキストのみの記事のため）
- 実際に提供できる内容のみをタイトルに含める

## 出力形式
**タイトル候補:**
1. [SEO最適化されたタイトル1]
2. [SEO最適化されたタイトル2] 
3. [SEO最適化されたタイトル3]
4. [SEO最適化されたタイトル4]
5. [SEO最適化されたタイトル5]

**推奨タイトル:** [上記の中で最もSEO効果が高いと思われるタイトル]

タイトル候補を作成してください。
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            st.error(f"タイトル生成エラー: {str(e)}")
            return None
    
    def extract_titles_only(self, response: str) -> Dict[str, Any]:
        """タイトル候補のみを抽出"""
        title_candidates = []
        for i in range(1, 6):
            pattern = rf'{i}\.\s*(.+?)(?:\n|$)'
            match = re.search(pattern, response)
            if match:
                title_candidates.append(match.group(1).strip())
        
        recommended_match = re.search(r'\*\*推奨タイトル:\*\*\s*(.+?)(?:\n|$)', response)
        recommended_title = recommended_match.group(1).strip() if recommended_match else ""
        
        return {
            "title_candidates": title_candidates,
            "recommended_title": recommended_title
        }
    
    def generate_outline(self, keyword: str, genre: str, target_audience: str, 
                        sub_keywords: str = "", article_length: str = "標準",
                        specific_approach: str = "") -> Optional[str]:
        """記事の目次・構成を生成"""
        if not self.client:
            return None
        
        length_guide = {
            "短め": "2000-3000文字程度（5-6セクション）",
            "標準": "3000-5000文字程度（6-8セクション）", 
            "長め": "5000-8000文字程度（8-10セクション）"
        }
        
        prompt = f"""
あなたはSEO対策に精通したプロのライターです。以下の条件に基づいて、詳細な記事の目次・構成を作成してください。

## 作成条件
- メインキーワード: {keyword}
- 記事ジャンル: {genre}
- 想定読者層: {target_audience}
- 記事の長さ: {length_guide.get(article_length, "3000-5000文字程度（6-8セクション）")}
"""
        
        if sub_keywords:
            prompt += f"- サブキーワード: {sub_keywords}\n"
        
        if specific_approach:
            prompt += f"- 特定の観点: {specific_approach}\n"
        
        prompt += """
## 構成要件
- 導入文（読者の関心を引く）
- 本文セクション（H2見出し）を6-10個程度
- 各セクションにH3サブセクションを2-3個含める
- まとめ・結論部分
- SEO効果の高い見出し構成

## 出力形式
**導入文:** [読者の関心を引く導入文・120-160文字程度]

**記事構成:**
## 1. [H2見出し1]
### 1-1. [H3サブ見出し1-1]
### 1-2. [H3サブ見出し1-2]

## 2. [H2見出し2]
### 2-1. [H3サブ見出し2-1]
### 2-2. [H3サブ見出し2-2]
### 2-3. [H3サブ見出し2-3]

## 3. [H2見出し3]
### 3-1. [H3サブ見出し3-1]
### 3-2. [H3サブ見出し3-2]

...

## まとめ
### まとめの要点1
### まとめの要点2

詳細な構成を作成してください。
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            st.error(f"構成生成エラー: {str(e)}")
            return None
    
    def generate_section(self, keyword: str, section_title: str, subsections: list, 
                        context: str = "") -> Optional[str]:
        """個別セクションを詳細に生成"""
        if not self.client:
            return None
        
        subsection_text = "\n".join([f"- {sub}" for sub in subsections])
        
        prompt = f"""
あなたはSEO対策に精通したプロのライターです。以下の条件に基づいて、記事の1つのセクションを詳細に執筆してください。

## 執筆条件
- メインキーワード: {keyword}
- セクションタイトル: {section_title}
- サブセクション:
{subsection_text}

## 記事の文脈
{context}

## 執筆要件
- セクション全体で600-1000文字程度
- 各サブセクションを詳しく解説
- 具体例、手順、tips等を豊富に含める
- 読者が実際に行動できる実践的な情報
- 専門的な内容も分かりやすく説明
- SEOキーワードを自然に含める
- 図表や画像の代わりに、詳細な文字による説明を提供
- 視覚的要素が必要な場合は「図表のイメージ」として文字で説明

## 出力形式
## {section_title}

### [サブセクション1]
[詳細な内容・具体例・手順等]

### [サブセクション2]  
[詳細な内容・具体例・手順等]

### [サブセクション3（あれば）]
[詳細な内容・具体例・手順等]

セクションを執筆してください。
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            st.error(f"セクション生成エラー: {str(e)}")
            return None
    
    def extract_outline_structure(self, outline: str) -> Dict[str, Any]:
        """構成から見出し構造を抽出"""
        sections = []
        current_section = None
        
        lines = outline.split('\n')
        for line in lines:
            line = line.strip()
            
            # H2見出しを検出
            if line.startswith('## ') and not line.startswith('## まとめ'):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': line.replace('## ', ''),
                    'subsections': []
                }
            
            # H3見出しを検出
            elif line.startswith('### ') and current_section:
                current_section['subsections'].append(line.replace('### ', ''))
        
        # 最後のセクションを追加
        if current_section:
            sections.append(current_section)
        
        # 導入文を抽出
        intro_match = re.search(r'\*\*導入文:\*\*\s*(.+?)(?:\n|$)', outline)
        intro = intro_match.group(1).strip() if intro_match else ""
        
        return {
            'intro': intro,
            'sections': sections
        }
    
    def extract_title_and_meta(self, article: str) -> Dict[str, str]:
        """導入文の抽出"""
        # 導入文を抽出
        intro_match = re.search(r'\*\*導入文:\*\*\s*(.+?)(?:\n|$)', article)
        intro = intro_match.group(1).strip() if intro_match else "導入文が見つかりません"
        
        return {"intro": intro}

def main():
    # ヘッダー
    st.markdown('<h1 class="main-header">📝 SEO記事生成ツール</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">初心者でも簡単にSEO対応のブログ記事を生成できます</p>', unsafe_allow_html=True)
    
    # セッション状態の初期化
    if 'generated_article' not in st.session_state:
        st.session_state.generated_article = ""
    if 'generation_completed' not in st.session_state:
        st.session_state.generation_completed = False
    if 'generated_titles' not in st.session_state:
        st.session_state.generated_titles = {}
    if 'selected_title' not in st.session_state:
        st.session_state.selected_title = ""
    if 'generation_progress' not in st.session_state:
        st.session_state.generation_progress = 0
    
    # サイドバーでAPI Key設定
    with st.sidebar:
        st.header("🔑 API設定")
        
        # SecretsからAPIキーを取得、なければ入力欄を表示
        if "ANTHROPIC_API_KEY" in st.secrets:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            st.success("APIキーが設定されています")
        else:
            api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                help="Anthropic Claude APIキーを入力してください"
            )
            if api_key:
                st.success("APIキーが設定されました")
            else:
                st.warning("APIキーを入力してください")
        
        st.header("📖 使い方ガイド")
        st.markdown("""
        1. APIキーを入力
        2. 必須項目を入力
        3. タイトル候補を生成・選択
        4. 「記事を生成」ボタンをクリック
        5. 生成された記事を確認・コピー
        """)
    
    # メインコンテンツ
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="input-section">', unsafe_allow_html=True)
        st.header("📝 記事情報入力")
        
        # ステップガイド
        st.markdown("""
        <div class="step-guide">
        <strong>ステップ 1:</strong> 以下の必須項目を入力してください
        </div>
        """, unsafe_allow_html=True)
        
        # 必須項目
        st.subheader("必須項目")
        keyword = st.text_input(
            "メインキーワード *",
            placeholder="例: Python プログラミング",
            help="記事のメインとなるキーワードを入力してください"
        )
        
        genre = st.selectbox(
            "記事のジャンル/カテゴリ *",
            options=["", "技術・プログラミング", "ビジネス", "ライフスタイル", "健康・美容", 
                    "教育・学習", "エンターテイメント", "旅行", "料理・グルメ", "ファッション", "その他"],
            help="記事のジャンルを選択してください"
        )
        
        target_audience = st.selectbox(
            "想定読者層 *",
            options=["", "初心者", "中級者", "上級者", "専門家", "一般向け"],
            help="記事を読む対象者を選択してください"
        )
        
        # タイトル生成ボタン
        if st.button("🎯 タイトル候補を生成", use_container_width=True):
            if not api_key:
                st.error("APIキーを入力してください")
            elif not keyword or len(keyword.strip()) < 2:
                st.error("メインキーワードは2文字以上で入力してください")
            else:
                generator = SEOBlogGenerator(api_key)
                with st.spinner("タイトル候補を生成中..."):
                    titles_response = generator.generate_titles(keyword, genre, target_audience)
                    if titles_response:
                        st.session_state.generated_titles = generator.extract_titles_only(titles_response)
                        st.success("タイトル候補が生成されました！")
                    else:
                        st.error("タイトル生成に失敗しました。APIキーを確認してください。")
        
        # タイトル候補の表示
        if 'generated_titles' in st.session_state and st.session_state.generated_titles:
            st.subheader("🎯 生成されたタイトル候補")
            titles_data = st.session_state.generated_titles
            
            if titles_data["title_candidates"]:
                # タイトル候補を表示
                st.write("**以下から記事のタイトルを選択してください：**")
                
                # ラジオボタンでタイトル選択
                title_options = []
                for i, title in enumerate(titles_data["title_candidates"], 1):
                    title_options.append(f"{i}. {title}")
                
                if title_options:
                    selected_title_index = st.radio(
                        "タイトルを選択:",
                        range(len(title_options)),
                        format_func=lambda x: title_options[x],
                        key="title_selection"
                    )
                    
                    # 選択されたタイトルを保存
                    st.session_state.selected_title = titles_data["title_candidates"][selected_title_index]
                    
                    # 選択されたタイトルを強調表示
                    st.success(f"**選択されたタイトル:** {st.session_state.selected_title}")
                
                # AI推奨タイトルも参考として表示
                if titles_data["recommended_title"]:
                    st.info(f"💡 **AI推奨:** {titles_data['recommended_title']}")
            
            st.markdown("---")
        
        # オプション項目
        st.subheader("オプション項目")
        sub_keywords = st.text_input(
            "サブキーワード",
            placeholder="例: 学習方法, 初心者向け",
            help="関連するキーワードがあれば入力してください（カンマ区切り）"
        )
        
        article_length = st.selectbox(
            "記事の長さ",
            options=["短め", "標準", "長め"],
            index=1,
            help="記事の長さを選択してください"
        )
        
        specific_approach = st.text_area(
            "特定の観点やアプローチ",
            placeholder="例: 実践的な手順を重視、初心者向けの説明を充実",
            help="記事で重視したい観点があれば入力してください"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 生成ボタン
        if st.button("🚀 記事を生成", type="primary", use_container_width=True):
            if not api_key:
                st.error("APIキーを入力してください")
            else:
                generator = SEOBlogGenerator(api_key)
                validation = generator.validate_inputs(keyword, genre, target_audience)
                
                if not validation["is_valid"]:
                    for error in validation["errors"]:
                        st.error(error)
                else:
                    # ステップバイステップ記事生成プロセス
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        # ステップ1: 構成生成
                        status_text.text("ステップ1/4: 記事構成を生成中...")
                        progress_bar.progress(25)
                        
                        outline = generator.generate_outline(
                            keyword, genre, target_audience, 
                            sub_keywords, article_length, specific_approach
                        )
                        
                        if not outline:
                            st.error("構成の生成に失敗しました。")
                            return
                        
                        # ステップ2: 構成解析
                        status_text.text("ステップ2/4: 構成を解析中...")
                        progress_bar.progress(35)
                        
                        structure = generator.extract_outline_structure(outline)
                        
                        # ステップ3: セクションごとに生成
                        status_text.text("ステップ3/4: セクションを詳細生成中...")
                        sections_content = []
                        
                        total_sections = len(structure['sections'])
                        for i, section in enumerate(structure['sections']):
                            section_progress = 35 + (50 * (i + 1) / total_sections)
                            progress_bar.progress(int(section_progress))
                            status_text.text(f"ステップ3/4: セクション {i+1}/{total_sections} を生成中...")
                            
                            section_content = generator.generate_section(
                                keyword, 
                                section['title'], 
                                section['subsections'],
                                f"記事テーマ: {keyword} ({genre})"
                            )
                            
                            if section_content:
                                sections_content.append(section_content)
                        
                        # ステップ4: 記事統合
                        status_text.text("ステップ4/4: 記事を統合中...")
                        progress_bar.progress(95)
                        
                        # 最終記事を統合
                        final_article = f"**導入文:** {structure['intro']}\n\n"
                        final_article += f"**記事本文:**\n\n"
                        
                        # 選択されたタイトルを使用
                        if 'selected_title' in st.session_state and st.session_state.selected_title:
                            final_article += f"# {st.session_state.selected_title}\n\n"
                        
                        final_article += f"{structure['intro']}\n\n"
                        
                        # 各セクションを追加
                        for content in sections_content:
                            final_article += content + "\n\n"
                        
                        # まとめを追加
                        final_article += f"## まとめ\n\n"
                        final_article += f"本記事では、{keyword}について詳しく解説しました。"
                        final_article += f"各ポイントを実践することで、{target_audience}の方でも効果的に活用できるでしょう。"
                        
                        progress_bar.progress(100)
                        status_text.text("✅ 記事生成完了！")
                        
                        st.session_state.generated_article = final_article
                        st.session_state.generation_completed = True
                        st.success(f"記事が正常に生成されました！（総セクション数: {len(sections_content)}）")
                        
                        # プログレスバーをクリア
                        time.sleep(1)
                        progress_bar.empty()
                        status_text.empty()
                        
                    except Exception as e:
                        st.error(f"記事生成中にエラーが発生しました: {str(e)}")
                        progress_bar.empty()
                        status_text.empty()
    
    with col2:
        st.markdown('<div class="output-section">', unsafe_allow_html=True)
        st.header("📄 生成された記事")
        
        if st.session_state.generation_completed and st.session_state.generated_article:
            # 記事の表示
            article = st.session_state.generated_article
            
            # タイトルとメタディスクリプションの抽出
            generator = SEOBlogGenerator()
            extracted = generator.extract_title_and_meta(article)
            
            # 記事情報の表示
            st.subheader("📋 記事情報")
            
            # 選択されたタイトルを表示
            if 'selected_title' in st.session_state and st.session_state.selected_title:
                st.write(f"**選択されたタイトル:** {st.session_state.selected_title}")
            else:
                st.write("**タイトル:** タイトルが選択されていません")
            
            # 記事本文の表示
            st.subheader("📝 記事本文")
            
            # 記事本文をそのまま表示（導入文も含める）
            st.markdown(article)
            
            # ダウンロード・コピー機能
            st.subheader("💾 ダウンロード・コピー")
            
            col_download1, col_download2 = st.columns(2)
            
            with col_download1:
                st.download_button(
                    label="📄 テキスト形式でダウンロード",
                    data=article,
                    file_name=f"seo_article_{keyword.replace(' ', '_').replace('　', '_')}.txt",
                    mime="text/plain"
                )
            
            with col_download2:
                st.download_button(
                    label="📝 Markdown形式でダウンロード",
                    data=article,
                    file_name=f"seo_article_{keyword.replace(' ', '_').replace('　', '_')}.md",
                    mime="text/markdown"
                )
            
            # コピー用テキストエリア
            st.text_area(
                "記事内容（コピー用）",
                value=article,
                height=200,
                help="この欄から記事をコピーできます"
            )
            
        else:
            st.info("左側の入力フォームに情報を入力して、「記事を生成」ボタンをクリックしてください。")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # フッター
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9em;">
    <p>SEO記事生成ツール | Powered by Anthropic Claude API</p>
    <p>⚠️ 生成された記事は必ず内容を確認してからご利用ください</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
