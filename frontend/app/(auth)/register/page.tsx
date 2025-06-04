'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-spinner';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/store/auth-store';
import { RegisterData } from '@/types';
import { EyeIcon, EyeSlashIcon, CheckIcon } from '@heroicons/react/24/outline';

interface RegisterFormData extends RegisterData {
  // All fields are already in RegisterData now
}

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormData>();

  const password = watch('password');

  const registerMutation = useMutation({
    mutationFn: async (data: RegisterData) => {
      const response = await authService.register(data);
      return response;
    },
    onSuccess: (data) => {
      setAuth(data.user, data.tokens);
      toast.success('Registration successful!');
      router.push('/dashboard');
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.errors
        ? Object.values(error.response.data.errors).flat().join(', ')
        : error.response?.data?.detail || 'Registration failed';
      toast.error(errorMessage);
    },
  });

  const onSubmit = (data: RegisterFormData) => {
    registerMutation.mutate(data);
  };

  const passwordRequirements = [
    { regex: /.{8,}/, text: 'At least 8 characters' },
    { regex: /[A-Z]/, text: 'One uppercase letter' },
    { regex: /[a-z]/, text: 'One lowercase letter' },
    { regex: /[0-9]/, text: 'One number' },
    { regex: /[^A-Za-z0-9]/, text: 'One special character' },
  ];

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Create an Account</CardTitle>
        <CardDescription>
          Start your free trial and manage your finances
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="firstName">First Name</Label>
                <Input
                  id="firstName"
                  type="text"
                  placeholder="John"
                  {...register('first_name', {
                    required: 'First name is required',
                  })}
                  autoComplete="given-name"
                />
                {errors.first_name && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.first_name.message}
                  </p>
                )}
              </div>
              <div>
                <Label htmlFor="lastName">Last Name</Label>
                <Input
                  id="lastName"
                  type="text"
                  placeholder="Doe"
                  {...register('last_name', {
                    required: 'Last name is required',
                  })}
                  autoComplete="family-name"
                />
                {errors.last_name && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.last_name.message}
                  </p>
                )}
              </div>
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                {...register('email', {
                  required: 'Email is required',
                  pattern: {
                    value: /\S+@\S+\.\S+/,
                    message: 'Invalid email address',
                  },
                })}
                autoComplete="email"
              />
              {errors.email && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.email.message}
                </p>
              )}
            </div>
            <div>
              <Label htmlFor="companyName">Company Name</Label>
              <Input
                id="companyName"
                type="text"
                placeholder="Acme Corp"
                {...register('company_name', {
                  required: 'Company name is required',
                })}
                autoComplete="organization"
              />
              {errors.company_name && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.company_name.message}
                </p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="companyType">Company Type</Label>
                <select
                  id="companyType"
                  {...register('company_type', {
                    required: 'Company type is required',
                  })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">Select type</option>
                  <option value="mei">MEI</option>
                  <option value="me">Microempresa</option>
                  <option value="epp">Empresa de Pequeno Porte</option>
                  <option value="ltda">Limitada</option>
                  <option value="sa">Sociedade Anônima</option>
                  <option value="other">Outros</option>
                </select>
                {errors.company_type && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.company_type.message}
                  </p>
                )}
              </div>
              <div>
                <Label htmlFor="businessSector">Business Sector</Label>
                <select
                  id="businessSector"
                  {...register('business_sector', {
                    required: 'Business sector is required',
                  })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">Select sector</option>
                  <option value="commerce">Comércio</option>
                  <option value="services">Serviços</option>
                  <option value="industry">Indústria</option>
                  <option value="technology">Tecnologia</option>
                  <option value="health">Saúde</option>
                  <option value="education">Educação</option>
                  <option value="food">Alimentação</option>
                  <option value="construction">Construção</option>
                  <option value="transport">Transporte</option>
                  <option value="agriculture">Agricultura</option>
                  <option value="other">Outros</option>
                </select>
                {errors.business_sector && (
                  <p className="text-sm text-red-500 mt-1">
                    {errors.business_sector.message}
                  </p>
                )}
              </div>
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Create a strong password"
                  {...register('password', {
                    required: 'Password is required',
                    validate: (value) => {
                      const failedRequirements = passwordRequirements.filter(
                        (req) => !req.regex.test(value)
                      );
                      if (failedRequirements.length > 0) {
                        return `Password must have: ${failedRequirements
                          .map((req) => req.text.toLowerCase())
                          .join(', ')}`;
                      }
                      return true;
                    },
                  })}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.password.message}
                </p>
              )}
              {password && (
                <div className="mt-2 space-y-1">
                  {passwordRequirements.map((req, index) => (
                    <div
                      key={index}
                      className={`flex items-center text-sm ${
                        req.regex.test(password)
                          ? 'text-green-600'
                          : 'text-gray-400'
                      }`}
                    >
                      <CheckIcon
                        className={`h-4 w-4 mr-1 ${
                          req.regex.test(password) ? 'visible' : 'invisible'
                        }`}
                      />
                      {req.text}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div>
              <Label htmlFor="password2">Confirm Password</Label>
              <div className="relative">
                <Input
                  id="password2"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm your password"
                  {...register('password2', {
                    required: 'Please confirm your password',
                    validate: (value) =>
                      value === password || 'Passwords do not match',
                  })}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showConfirmPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>
              {errors.password2 && (
                <p className="text-sm text-red-500 mt-1">
                  {errors.password2.message}
                </p>
              )}
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <Button
            type="submit"
            className="w-full"
            disabled={registerMutation.isPending}
          >
            {registerMutation.isPending ? <LoadingSpinner /> : 'Create Account'}
          </Button>
          <p className="text-sm text-center text-gray-600">
            By signing up, you agree to our{' '}
            <Link href="#" className="text-primary hover:underline">
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link href="#" className="text-primary hover:underline">
              Privacy Policy
            </Link>
          </p>
          <p className="text-sm text-center text-gray-600">
            Already have an account?{' '}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}