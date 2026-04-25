// 모든 API 요청의 기본 주소
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8080/api"; // 환경 변수에서 API 주소를 읽어오고, 없으면 로컬 주소 사용

// 에러 응답 본문에서 사용자에게 보여줄 메시지 추출
const parseErrorMessage = async (response) => {
  try {
    const data = await response.json(); // JSON으로 파싱 시도
    // FastAPI는 detail 필드 사용, 일반적인 경우 message 필드 사용
    return data.detail || data.message || JSON.stringify(data);
  } catch {
    return response.statusText || "요청 처리 중 오류가 발생했습니다.";
  }
};

// 공통 HTTP 요청 함수: 성공/실패/204 처리 규칙을 한 곳에서 관리
export const apiRequest = async (path, options = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        // JSON API 기본 헤더
        "Content-Type": "application/json", // 요청 본문이 JSON임을 명시
        ...options.headers,
      }, // 추가 옵션 병합 (예: method, body)
      ...options, // method, body 등 추가 옵션
    });

    // 2xx가 아니면 에러로 처리
    if (!response.ok) {
      const message = await parseErrorMessage(response);
      throw new Error(`[${response.status}] ${message}`);
    }

    // DELETE처럼 응답 바디가 없는 경우
    if (response.status === 204) {
      return null;
    }

    // 기본은 JSON으로 파싱
    return response.json();
  } catch (err) {
    // 네트워크 오류 또는 서버 연결 실패
    if (err.message.includes('[')) {
      // 이미 서버에서 받은 에러 메시지
      throw err;
    }
    // fetch 자체가 실패한 경우 (네트워크 오류, 서버 다운 등)
    throw new Error('서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
  }
};
