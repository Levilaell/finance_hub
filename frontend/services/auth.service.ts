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

  async enable2FA() {
    return apiClient.post("/api/auth/2fa/enable/");
  }

  async disable2FA(data: { password: string }) {
    return apiClient.post("/api/auth/2fa/disable/", data);
  }

  async verify2FA(data: { code: string }): Promise<TwoFactorVerifyResponse> {
    return apiClient.post("/api/auth/2fa/verify/", data);
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