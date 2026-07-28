import {Injectable, signal} from '@angular/core';

export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
  message: string;
  type: ToastType;
}

@Injectable({
  providedIn: 'root'
})
export class ToasterService {
  private readonly activeToast = signal<Toast | null>(null);
  private dismissTimer?: ReturnType<typeof setTimeout>;

  readonly toast = this.activeToast.asReadonly();

  show(message: string, type: ToastType, duration = 3500): void {
    clearTimeout(this.dismissTimer);
    this.activeToast.set({message, type});
    this.dismissTimer = setTimeout(() => this.dismiss(), duration);
  }

  success(message: string): void {
    this.show(message, 'success');
  }

  error(message: string): void {
    this.show(message, 'error', 5000);
  }

  info(message: string): void {
    this.show(message, 'info');
  }

  dismiss(): void {
    clearTimeout(this.dismissTimer);
    this.activeToast.set(null);
  }
}
