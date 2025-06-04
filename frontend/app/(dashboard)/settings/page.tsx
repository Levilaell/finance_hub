'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/store/auth-store';
import { User } from '@/types';
import { 
  UserIcon,
  ShieldCheckIcon,
  CreditCardIcon,
  BellIcon,
  EyeIcon,
  EyeSlashIcon,
  KeyIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface ProfileForm {
  first_name: string;
  last_name: string;
  email: string;
}

interface PasswordForm {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { user, setUser } = useAuthStore();
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [is2FADialogOpen, setIs2FADialogOpen] = useState(false);
  const [qrCode, setQrCode] = useState<string>('');
  const [twoFactorCode, setTwoFactorCode] = useState('');

  const profileForm = useForm<ProfileForm>({
    defaultValues: {
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      email: user?.email || '',
    },
  });

  const passwordForm = useForm<PasswordForm>();

  const updateProfileMutation = useMutation({
    mutationFn: (data: Partial<User>) => authService.updateProfile(data),
    onSuccess: (updatedUser) => {
      setUser(updatedUser);
      toast.success('Profile updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      authService.changePassword(data),
    onSuccess: () => {
      passwordForm.reset();
      toast.success('Password changed successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to change password');
    },
  });

  const enable2FAMutation = useMutation({
    mutationFn: () => authService.enable2FA(),
    onSuccess: (data) => {
      setQrCode(data.qr_code);
      setIs2FADialogOpen(true);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to enable 2FA');
    },
  });

  const verify2FAMutation = useMutation({
    mutationFn: () => authService.verify2FA({ code: twoFactorCode }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      setIs2FADialogOpen(false);
      setTwoFactorCode('');
      toast.success('Two-factor authentication enabled successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Invalid verification code');
    },
  });

  const disable2FAMutation = useMutation({
    mutationFn: (password: string) => authService.disable2FA({ password }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      toast.success('Two-factor authentication disabled');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to disable 2FA');
    },
  });

  const onProfileSubmit = (data: ProfileForm) => {
    updateProfileMutation.mutate(data);
  };

  const onPasswordSubmit = (data: PasswordForm) => {
    if (data.new_password !== data.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    changePasswordMutation.mutate({
      current_password: data.current_password,
      new_password: data.new_password,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-gray-600">Manage your account settings and preferences</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="ai">AI & Rules</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>

        {/* Profile Settings */}
        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <UserIcon className="h-5 w-5 mr-2" />
                Profile Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="first_name">First Name</Label>
                    <Input
                      id="first_name"
                      {...profileForm.register('first_name', { required: true })}
                    />
                  </div>
                  <div>
                    <Label htmlFor="last_name">Last Name</Label>
                    <Input
                      id="last_name"
                      {...profileForm.register('last_name', { required: true })}
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    {...profileForm.register('email', { required: true })}
                  />
                </div>
                <div className="pt-4">
                  <Button
                    type="submit"
                    disabled={updateProfileMutation.isPending}
                  >
                    {updateProfileMutation.isPending ? (
                      <LoadingSpinner />
                    ) : (
                      'Update Profile'
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security" className="space-y-4">
          {/* Change Password */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <KeyIcon className="h-5 w-5 mr-2" />
                Change Password
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-4">
                <div>
                  <Label htmlFor="current_password">Current Password</Label>
                  <div className="relative">
                    <Input
                      id="current_password"
                      type={showCurrentPassword ? 'text' : 'password'}
                      {...passwordForm.register('current_password', { required: true })}
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
                    >
                      {showCurrentPassword ? (
                        <EyeSlashIcon className="h-5 w-5" />
                      ) : (
                        <EyeIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                </div>
                <div>
                  <Label htmlFor="new_password">New Password</Label>
                  <div className="relative">
                    <Input
                      id="new_password"
                      type={showNewPassword ? 'text' : 'password'}
                      {...passwordForm.register('new_password', {
                        required: true,
                        minLength: 8,
                      })}
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
                    >
                      {showNewPassword ? (
                        <EyeSlashIcon className="h-5 w-5" />
                      ) : (
                        <EyeIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                </div>
                <div>
                  <Label htmlFor="confirm_password">Confirm New Password</Label>
                  <div className="relative">
                    <Input
                      id="confirm_password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      {...passwordForm.register('confirm_password', { required: true })}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
                    >
                      {showConfirmPassword ? (
                        <EyeSlashIcon className="h-5 w-5" />
                      ) : (
                        <EyeIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                </div>
                <div className="pt-4">
                  <Button
                    type="submit"
                    disabled={changePasswordMutation.isPending}
                  >
                    {changePasswordMutation.isPending ? (
                      <LoadingSpinner />
                    ) : (
                      'Change Password'
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Two-Factor Authentication */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <ShieldCheckIcon className="h-5 w-5 mr-2" />
                Two-Factor Authentication
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  Add an extra layer of security to your account by enabling two-factor authentication.
                </p>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">
                      Two-Factor Authentication is {user?.is_two_factor_enabled ? 'enabled' : 'disabled'}
                    </p>
                    <p className="text-sm text-gray-600">
                      {user?.is_two_factor_enabled
                        ? 'Your account is protected with 2FA'
                        : 'Enable 2FA to secure your account'}
                    </p>
                  </div>
                  {user?.is_two_factor_enabled ? (
                    <Button
                      variant="outline"
                      onClick={() => {
                        const password = prompt('Enter your password to disable 2FA:');
                        if (password) {
                          disable2FAMutation.mutate(password);
                        }
                      }}
                      disabled={disable2FAMutation.isPending}
                    >
                      Disable 2FA
                    </Button>
                  ) : (
                    <Button
                      onClick={() => enable2FAMutation.mutate()}
                      disabled={enable2FAMutation.isPending}
                    >
                      {enable2FAMutation.isPending ? <LoadingSpinner /> : 'Enable 2FA'}
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI & Categorization Rules */}
        <TabsContent value="ai" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                </svg>
                AI Categorization Settings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="font-medium mb-4">Automatic Categorization</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Enable AI Categorization</p>
                        <p className="text-sm text-gray-600">
                          Automatically categorize transactions using AI
                        </p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Auto-apply high confidence suggestions</p>
                        <p className="text-sm text-gray-600">
                          Automatically apply categories when AI confidence is above 90%
                        </p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Learning from corrections</p>
                        <p className="text-sm text-gray-600">
                          Improve AI accuracy by learning from manual corrections
                        </p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium mb-4">Performance Metrics</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Accuracy</p>
                      <p className="text-2xl font-bold text-green-600">92%</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Auto-categorized</p>
                      <p className="text-2xl font-bold text-blue-600">1,234</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600">Manual reviews</p>
                      <p className="text-2xl font-bold text-orange-600">89</p>
                    </div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-medium">Custom Rules</h3>
                    <Button variant="outline" size="sm">
                      Add Rule
                    </Button>
                  </div>
                  <div className="space-y-3">
                    <div className="border rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">Contains "Uber" → Transportation</p>
                          <p className="text-sm text-gray-600">
                            Keyword match rule • Active
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="ghost" size="sm">Edit</Button>
                          <Button variant="ghost" size="sm" className="text-red-600">Delete</Button>
                        </div>
                      </div>
                    </div>
                    <div className="border rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">Amount &gt; $500 → Large Expense</p>
                          <p className="text-sm text-gray-600">
                            Amount-based rule • Active
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="ghost" size="sm">Edit</Button>
                          <Button variant="ghost" size="sm" className="text-red-600">Delete</Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4">
                  <Button>Save AI Settings</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Billing Settings */}
        <TabsContent value="billing">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <CreditCardIcon className="h-5 w-5 mr-2" />
                Billing & Subscription
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="font-medium mb-2">Current Plan</h3>
                  <div className="border rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">{user?.company?.subscription_plan?.name || 'Free Trial'}</p>
                        <p className="text-sm text-gray-600">
                          {user?.company?.subscription_plan?.price 
                            ? `$${user.company.subscription_plan.price}/${user.company.subscription_plan.interval}`
                            : 'No charge during trial period'
                          }
                        </p>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          user?.company?.subscription_status === 'active'
                            ? 'bg-green-100 text-green-800'
                            : user?.company?.subscription_status === 'trialing'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user?.company?.subscription_status}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {user?.company?.trial_ends_at && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm text-blue-700">
                      Your trial ends on {new Date(user.company.trial_ends_at).toLocaleDateString()}.
                      Upgrade to continue using all features.
                    </p>
                  </div>
                )}

                <div className="space-y-2">
                  <Button className="w-full sm:w-auto">
                    Upgrade Plan
                  </Button>
                  <Button variant="outline" className="w-full sm:w-auto ml-0 sm:ml-2">
                    View Billing History
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notification Settings */}
        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BellIcon className="h-5 w-5 mr-2" />
                Notification Preferences
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Email Notifications</p>
                      <p className="text-sm text-gray-600">
                        Receive email updates about your account activity
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Transaction Alerts</p>
                      <p className="text-sm text-gray-600">
                        Get notified about new transactions
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Low Balance Warnings</p>
                      <p className="text-sm text-gray-600">
                        Alert when account balance is low
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Monthly Reports</p>
                      <p className="text-sm text-gray-600">
                        Receive monthly financial summaries
                      </p>
                    </div>
                    <Switch defaultChecked />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Security Alerts</p>
                      <p className="text-sm text-gray-600">
                        Important security and account notifications
                      </p>
                    </div>
                    <Switch defaultChecked disabled />
                  </div>
                </div>

                <div className="pt-4">
                  <Button>Save Preferences</Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-red-200">
            <CardHeader>
              <CardTitle className="flex items-center text-red-600">
                <TrashIcon className="h-5 w-5 mr-2" />
                Danger Zone
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="font-medium text-red-600">Delete Account</p>
                  <p className="text-sm text-gray-600">
                    Permanently delete your account and all associated data. This action cannot be undone.
                  </p>
                </div>
                <Button variant="destructive">
                  Delete Account
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 2FA Setup Dialog */}
      <Dialog open={is2FADialogOpen} onOpenChange={setIs2FADialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Enable Two-Factor Authentication</DialogTitle>
            <DialogDescription>
              Scan the QR code with your authenticator app and enter the verification code
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {qrCode && (
              <div className="flex justify-center">
                <img src={qrCode} alt="2FA QR Code" className="w-48 h-48" />
              </div>
            )}
            <div>
              <Label htmlFor="2fa-code">Verification Code</Label>
              <Input
                id="2fa-code"
                type="text"
                placeholder="000000"
                maxLength={6}
                value={twoFactorCode}
                onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, ''))}
                className="text-center text-2xl tracking-widest"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIs2FADialogOpen(false);
                setTwoFactorCode('');
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={() => verify2FAMutation.mutate()}
              disabled={verify2FAMutation.isPending || twoFactorCode.length !== 6}
            >
              {verify2FAMutation.isPending ? <LoadingSpinner /> : 'Verify & Enable'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}