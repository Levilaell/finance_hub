import apiClient from "@/lib/api-client";
import { User, LoginCredentials, RegisterData, LoginResponse, TwoFactorVerifyResponse } from "@/types";

class AuthService {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    return apiClient.login(credentials.email, credentials.password);
  }

  async loginWith2FA(email: string, password: string, twoFactorCode: string): Promise<LoginResponse> {
    return apiClient.login(email, password, twoFactorCode);
  }

  async register(data: RegisterData) {
    return apiClient.register(data);
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    return apiClient.patch<User>("/api/auth/profile/", data);
  }

  async changePassword(data: {
    current_password: string;
    new_password: string;
  }) {
    return apiClient.post("/api/auth/change-password/", {
      old_password: data.current_password,
      new_password: data.new_password
    });
  }

  async requestPasswordReset(email: string) {
    return apiClient.post("/api/auth/password-reset/", { email });
  }


  async deleteAccount(data: { password: string; confirmation: string }) {
    return apiClient.post("/api/auth/delete-account/", data);
  }
}

export const authService = new AuthService();