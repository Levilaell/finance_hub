import apiClient from "@/lib/api-client";
import { User, LoginCredentials, RegisterData, LoginResponse, TwoFactorVerifyResponse } from "@/types";

class AuthService {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    return apiClient.login(credentials.email, credentials.password);
  }

  async register(data: RegisterData) {
    return apiClient.register(data);
  }

  async logout() {
    return apiClient.logout();
  }

  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>("/api/auth/profile/");
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    return apiClient.patch<User>("/api/auth/profile/", data);
  }

  async changePassword(data: {
    current_password: string;
    new_password: string;
  }) {
    return apiClient.post("/api/auth/change-password/", data);
  }

  async setup2FA() {
    return apiClient.get<{ qr_code: string; backup_codes_count: number; setup_complete: boolean }>("/api/auth/2fa/setup/");
  }

  async enable2FA(token: string) {
    return apiClient.post<{ message: string; backup_codes: string[] }>("/api/auth/2fa/enable/", { token });
  }

  async disable2FA(data: { password: string }) {
    return apiClient.post("/api/auth/2fa/disable/", data);
  }

  async loginWith2FA(email: string, password: string, two_fa_code: string): Promise<LoginResponse> {
    return apiClient.login(email, password, two_fa_code);
  }

  async requestPasswordReset(email: string) {
    return apiClient.post("/api/auth/password-reset/", { email });
  }

  async resetPassword(data: {
    token: string;
    new_password: string;
  }) {
    return apiClient.post("/api/auth/password-reset/confirm/", data);
  }
}

export const authService = new AuthService();