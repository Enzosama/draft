import React, { useState } from 'react';
import { User } from '../data/types';

type AuthMode = 'login' | 'register' | 'forgot-password';

interface AuthModalProps {
  mode: AuthMode;
  onSwitchMode: (mode: AuthMode) => void;
  onAuthSuccess: (user: User) => void;
}

const AuthModal: React.FC<AuthModalProps> = ({ mode, onSwitchMode, onAuthSuccess }) => {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    const email = String(formData.get('email'));
    const password = String(formData.get('password'));
    setError(null)
    setLoading(true)

    if (mode === 'forgot-password') {
      try {
        const res = await fetch('/api/recover', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email })
        });

        if (res.ok) {
          alert('Nếu email của bạn tồn tại trong hệ thống, một liên kết đặt lại mật khẩu đã được gửi.');
          onSwitchMode('login');
        } else {
          setError('Không thể gửi yêu cầu. Vui lòng thử lại sau.');
        }
      } catch (err) {
        setError('Lỗi kết nối. Vui lòng kiểm tra mạng.');
      } finally {
        setLoading(false);
      }
      return;
    }

    if (mode === 'register') {
      const name = String(formData.get('name'));
      const confirm = String(formData.get('confirm-password'));
      const phone = String(formData.get('phone'));
      if (password !== confirm) {
        setError('Mật khẩu xác nhận không khớp')
        setLoading(false)
        return;
      }
      try {
        const res = await fetch('/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, fullname: name, phone, password })
        });
        if (res.ok) {
          setError(null)
          setLoading(false)
          alert('Đăng ký thành công! Vui lòng đăng nhập.');
          onSwitchMode('login');
          return;
        } else {
          let errorMessage = 'Vui lòng thử lại';
          try {
            // Read response as text first (can only read once)
            const responseText = await res.text();

            // Try to parse as JSON
            try {
              const errorData = JSON.parse(responseText);
              errorMessage = errorData.detail || errorMessage;
            } catch {
              // If not JSON, use text as error message
              errorMessage = responseText || errorMessage;
            }
          } catch (parseErr) {
            // If all parsing fails, use status text
            errorMessage = res.statusText || 'Vui lòng thử lại';
          }
          setError(`Đăng ký thất bại: ${errorMessage}`)
          setLoading(false)
          return;
        }
      } catch (err: any) {
        setError(`Đăng ký thất bại: ${err.message || 'Vui lòng thử lại'}`)
        setLoading(false)
        return;
      }
    }

    if (mode === 'login') {
      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        if (!res.ok) {
          let errorMessage = 'Sai email hoặc mật khẩu';
          try {
            // Read response as text first (can only read once)
            const responseText = await res.text();

            // Try to parse as JSON
            try {
              const errorData = JSON.parse(responseText);
              errorMessage = errorData.detail || errorMessage;
            } catch {
              // If not JSON, use text as error message
              errorMessage = responseText || errorMessage;
            }
          } catch (parseErr) {
            // If all parsing fails, use status text
            errorMessage = res.statusText || 'Sai email hoặc mật khẩu';
          }
          setError(errorMessage)
          setLoading(false)
          return;
        }
        const data = await res.json();
        const token = data.access_token as string;
        localStorage.setItem('token', token);
        const meRes = await fetch('/api/users/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (meRes.ok) {
          const me = await meRes.json();
          onAuthSuccess({ name: me.fullname, email: me.email, role: me.role || 'student' });
          setError(null)
        } else {
          setError('Không lấy được thông tin người dùng')
        }
        setLoading(false)
      } catch (err: any) {
        setError(`Đăng nhập thất bại: ${err.message || 'Vui lòng thử lại'}`)
        setLoading(false)
      }
    }
  };

  const inputBaseClasses = "appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm";

  return (
    <div className="flex-grow flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        <div className="bg-white p-8 rounded-xl shadow-lg space-y-8">
          <div>
            <h2 className="text-center text-3xl font-extrabold text-gray-900">
              {mode === 'login' ? 'Đăng nhập' : mode === 'register' ? 'Tạo tài khoản' : 'Quên mật khẩu'}
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              {mode === 'forgot-password' ? (
                'Nhập email để nhận liên kết đặt lại mật khẩu.'
              ) : (
                <>
                  Hoặc{' '}
                  <button onClick={() => onSwitchMode(mode === 'login' ? 'register' : 'login')} className="font-medium text-blue-600 hover:text-blue-500">
                    {mode === 'login' ? 'tạo tài khoản mới' : 'đăng nhập ngay'}
                  </button>
                </>
              )}
            </p>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            {mode === 'forgot-password' ? (
              <div className="rounded-md shadow-sm">
                <div>
                  <label htmlFor="email-address" className="sr-only">Địa chỉ email</label>
                  <input id="email-address" name="email" type="email" autoComplete="email" required className={`${inputBaseClasses} rounded-md`} placeholder="Địa chỉ email" />
                </div>
              </div>
            ) : (
              <div className="rounded-md shadow-sm -space-y-px">
                {mode === 'register' && (
                  <div>
                    <label htmlFor="name" className="sr-only">Họ và tên</label>
                    <input id="name" name="name" type="text" required className={`${inputBaseClasses} rounded-t-md`} placeholder="Họ và tên" />
                  </div>
                )}
                <div>
                  <label htmlFor="email-address" className="sr-only">Địa chỉ email</label>
                  <input id="email-address" name="email" type="email" autoComplete="email" required className={`${inputBaseClasses} ${mode === 'login' ? 'rounded-t-md' : ''}`} placeholder="Địa chỉ email" />
                </div>
                {mode === 'register' && (
                  <div>
                    <label htmlFor="phone" className="sr-only">Số điện thoại</label>
                    <input id="phone" name="phone" type="tel" required className={`${inputBaseClasses}`} placeholder="Số điện thoại" />
                  </div>
                )}
                <div>
                  <label htmlFor="password" className="sr-only">Mật khẩu</label>
                  <input id="password" name="password" type="password" autoComplete="current-password" required className={`${inputBaseClasses} ${mode === 'register' ? '' : 'rounded-b-md'}`} placeholder="Mật khẩu" />
                </div>
                {mode === 'register' && (
                  <div>
                    <label htmlFor="confirm-password" className="sr-only">Xác nhận mật khẩu</label>
                    <input id="confirm-password" name="confirm-password" type="password" required className={`${inputBaseClasses} rounded-b-md`} placeholder="Xác nhận mật khẩu" />
                  </div>
                )}
              </div>
            )}


            {mode === 'login' && (
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input id="remember-me" name="remember-me" type="checkbox" className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                  <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                    Ghi nhớ đăng nhập
                  </label>
                </div>
                <div className="text-sm">
                  <button type="button" onClick={() => onSwitchMode('forgot-password')} className="font-medium text-blue-600 hover:text-blue-500">
                    Quên mật khẩu?
                  </button>
                </div>
              </div>
            )}

            <div>
              <button type="submit" className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-[#1e40af] hover:bg-blue-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors">
                {mode === 'login' ? 'Đăng nhập' : mode === 'register' ? 'Đăng ký' : 'Gửi liên kết'}
              </button>
            </div>
            {mode === 'forgot-password' && (
              <div className="text-sm text-center mt-4">
                <button type="button" onClick={() => onSwitchMode('login')} className="font-medium text-blue-600 hover:text-blue-500">
                  &larr; Quay lại đăng nhập
                </button>
              </div>
            )}
          </form>
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
