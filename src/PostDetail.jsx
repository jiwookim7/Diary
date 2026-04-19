import { useEffect, useState } from 'react';
import { createComment, deleteComment, getComments } from './api/commentApi';
import './PostDetail.css';

export default function PostDetail({ post, onClose, currentUserId }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadComments();
  }, [post.id]);

  const loadComments = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getComments(post.id);
      setComments(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    
    if (!newComment.trim()) {
      setError('댓글 내용을 입력해주세요.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      await createComment({
        post_id: post.id,
        user_id: parseInt(currentUserId),
        content: newComment,
      });
      setNewComment('');
      await loadComments();
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteComment = async (commentId) => {
    if (!confirm('댓글을 삭제하시겠습니까?')) return;

    try {
      await deleteComment(commentId);
      await loadComments();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-content">
        <button className="modal-close" onClick={onClose}>
          ✕
        </button>

        {/* 일기 내용 */}
        <div className="post-detail-header">
          <div className="post-detail-date">
            {post.created_at ? new Date(post.created_at).toLocaleDateString('ko-KR', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              weekday: 'long'
            }) : ''}
          </div>
          <h2 className="post-detail-title">{post.title}</h2>
        </div>

        <div className="post-detail-content">
          {post.content}
        </div>

        <div className="divider"></div>

        {/* 댓글 섹션 */}
        <div className="comments-section">
          <h3 className="comments-title">
            💬 댓글 <span className="comments-count">{comments.length}</span>
          </h3>

          {/* 댓글 작성 폼 */}
          <form onSubmit={handleSubmitComment} className="comment-form">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="댓글을 입력하세요..."
              className="comment-input"
              rows={3}
            />
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="comment-submit-btn" disabled={submitting}>
              {submitting ? '등록 중...' : '댓글 등록'}
            </button>
          </form>

          {/* 댓글 목록 */}
          <div className="comments-list">
            {loading && <p className="loading-text">댓글을 불러오는 중...</p>}
            
            {!loading && comments.length === 0 && (
              <p className="empty-comments">첫 댓글을 작성해보세요!</p>
            )}

            {comments.map((comment) => (
              <div key={comment.id} className="comment-item">
                <div className="comment-header">
                  <span className="comment-author">👤 사용자 {comment.user_id}</span>
                  <span className="comment-date">
                    {new Date(comment.created_at).toLocaleString('ko-KR', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                </div>
                <p className="comment-content">{comment.content}</p>
                {comment.user_id === parseInt(currentUserId) && (
                  <button
                    className="comment-delete-btn"
                    onClick={() => handleDeleteComment(comment.id)}
                  >
                    삭제
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
