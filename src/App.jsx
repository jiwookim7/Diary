import { useEffect, useState } from "react";
import { createPost, deletePost, getPostList } from "./api/postApi";
import Login from "./Login.jsx";
import Signup from "./Signup.jsx";
import PostDetail from "./PostDetail.jsx";
import "./App.css";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  
  // 목록 데이터
  const [items, setItems] = useState([]);
  // 목록 로딩 상태
  const [loading, setLoading] = useState(true);
  // API 에러 메시지
  const [error, setError] = useState("");
  // 입력 폼 상태
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  // 저장 버튼 중복 클릭 방지
  const [submitting, setSubmitting] = useState(false);
  // 로그인한 사용자명
  const [username, setUsername] = useState("");
  // 선택된 글 (모달)
  const [selectedPost, setSelectedPost] = useState(null);

  // 서버에서 글 목록을 읽어와 화면 상태를 갱신
  const loadPosts = async () => {
    setLoading(true); // 로딩 상태 시작
    setError(""); // 이전 에러 메시지 초기화

    try {
      const list = await getPostList(); // API 요청으로 글 목록 조회
      setItems(list); // 조회된 목록으로 화면 상태 갱신
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // 로그인 상태 확인
  useEffect(() => {
    const storedUsername = localStorage.getItem('username');
    setIsAuthenticated(!!storedUsername);
    if (storedUsername) {
      setUsername(storedUsername);
    }

    // URL hash로 회원가입/로그인 페이지 구분
    const handleHashChange = () => {
      setShowSignup(window.location.hash === '#signup');
    };
    
    handleHashChange();
    window.addEventListener('hashchange', handleHashChange);
    
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // 첫 화면 렌더 시 1회 목록 조회 (인증된 경우만)
  useEffect(() => {
    if (isAuthenticated) {
      loadPosts();
    }
  }, [isAuthenticated]);

  const handleLoginSuccess = () => {
    const storedUsername = localStorage.getItem('username');
    setUsername(storedUsername);
    setIsAuthenticated(true);
    window.location.hash = '';
  };

  const handleLogout = () => {
    localStorage.removeItem('username');
    localStorage.removeItem('userId');
    setIsAuthenticated(false);
    setUsername('');
    window.location.hash = '';
  };

  // 인증되지 않은 경우 로그인/회원가입 화면
  if (!isAuthenticated) {
    return showSignup ? (
      <Signup />
    ) : (
      <Login onLoginSuccess={handleLoginSuccess} />
    );
  }

  // 글 저장 버튼 클릭 시 실행
  const handleSubmit = async (event) => {
    // form 기본 새로고침 동작 방지
    event.preventDefault();

    // 빈 문자열 제출 방지
    if (!title.trim() || !content.trim()) {
      setError("제목과 내용을 입력해 주세요.");
      return;
    }

    setSubmitting(true); // 중복 클릭 방지 위해 제출 상태 설정
    setError(""); // 이전 에러 메시지 초기화

    try {
      const userId = localStorage.getItem('userId');
      await createPost({ user_id: parseInt(userId), title, content }); //API 요청으로 글 저장
      setTitle(""); //저장 후 입력 폼 초기화
      setContent(""); //저장 후 입력 폼 초기화
      await loadPosts(); //저장 후 목록 새로고침으로 최신 상태 반영
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false); //저장 요청 완료 후 제출 상태 해제
    }
  };

  // 삭제 버튼 클릭 시 실행
  const handleDelete = async (id, event) => {
    // 이벤트 전파 중단 (카드 클릭 방지)
    event.stopPropagation();
    
    if (!confirm('정말 삭제하시겠습니까?')) return;
    
    try {
      await deletePost(id);
      await loadPosts();
    } catch (e) {
      setError(e.message);
    }
  };

  // 카드 클릭 시 모달 열기
  const handleCardClick = (post) => {
    setSelectedPost(post);
  };

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="header-left">
          <h1 className="app-title">✨ My Diary</h1>
          <p className="app-subtitle">당신의 일상을 기록하세요</p>
        </div>
        <div className="header-right">
          <div className="user-badge">
            <span className="user-avatar">👤</span>
            <span className="user-name">{username}</span>
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            로그아웃
          </button>
        </div>
      </header>

      {/* 글 작성 영역 */}
      <section className="write-section">
        <div className="section-header">
          <h2>✍️ 새 일기 작성</h2>
        </div>
        <form onSubmit={handleSubmit} className="write-form">
          <div className="form-group">
            <label htmlFor="title">제목</label>
            <input
              id="title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="오늘의 제목을 입력하세요"
              className="title-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="content">내용</label>
            <textarea
              id="content"
              rows={6}
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="오늘 하루는 어땠나요? 자유롭게 기록해보세요..."
              className="content-textarea"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="submit-btn" disabled={submitting}>
            {submitting ? "💾 저장 중..." : "📝 일기 저장"}
          </button>
        </form>
      </section>

      {/* 글 목록 영역 */}
      <section className="posts-section">
        <div className="section-header">
          <div>
            <h2>내 일기</h2>
            <p className="section-subtitle">총 {items.length}개의 일기</p>
          </div>
          <button type="button" className="refresh-btn" onClick={loadPosts}>
            🔄 새로고침
          </button>
        </div>

        {loading && (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>일기를 불러오는 중...</p>
            {items.length === 0 && <p className="loading-hint">서버가 시작 중이라면 최대 1분 정도 걸릴 수 있습니다.</p>}
          </div>
        )}
        
        {!loading && items.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">📝</div>
            <h3>아직 작성된 일기가 없어요</h3>
            <p>첫 일기를 작성해보세요!</p>
          </div>
        )}

        <div className="posts-grid">
          {items.map((item) => (
            <article 
              key={item.id} 
              className="post-card"
              onClick={() => handleCardClick(item)}
            >
              <div className="post-card-header">
                <div className="post-date">
                  {item.created_at ? new Date(item.created_at).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  }) : ''}
                </div>
                <button 
                  type="button" 
                  className="delete-icon-btn"
                  onClick={(e) => handleDelete(item.id, e)}
                  aria-label="삭제"
                >
                  🗑️
                </button>
              </div>
              <h3 className="post-card-title">{item.title || "(제목 없음)"}</h3>
              <p className="post-card-content">{item.content || "(내용 없음)"}</p>
            </article>
          ))}
        </div>

        {/* 에러가 있을 때만 표시 */}
        {error && <p className="error">{error}</p>}
      </section>

      {/* 일기 상세보기 모달 */}
      {selectedPost && (
        <PostDetail
          post={selectedPost}
          onClose={() => setSelectedPost(null)}
          currentUserId={localStorage.getItem('userId')}
        />
      )}
    </main>
  );
}

export default App;
