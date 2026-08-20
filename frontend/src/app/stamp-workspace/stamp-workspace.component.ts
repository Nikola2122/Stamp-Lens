import {CommonModule, NgOptimizedImage} from '@angular/common';
import {Component, ElementRef, OnInit, inject, signal, viewChild} from '@angular/core';
import {Router} from '@angular/router';
import {finalize, forkJoin} from 'rxjs';

import {StampImageService} from '../service/stamp-image.service';
import {StampImageModel} from '../models/StampImageModel';
import {ToasterComponent} from '../shared/toaster/toaster.component';
import {ToasterService} from '../shared/toaster/toaster.service';
import {ConfirmationModalComponent} from '../shared/confirmation-modal/confirmation-modal.component';

@Component({
  selector: 'app-stamp-workspace',
  imports: [CommonModule, ConfirmationModalComponent, ToasterComponent],
  templateUrl: './stamp-workspace.component.html',
  styleUrl: './stamp-workspace.component.scss'
})
export class StampWorkspaceComponent implements OnInit {
  private readonly imageService = inject(StampImageService);
  private readonly router = inject(Router);
  private readonly toaster = inject(ToasterService);
  private readonly fileInput = viewChild<ElementRef<HTMLInputElement>>('fileInput');
  private readonly carouselTrack = viewChild<ElementRef<HTMLElement>>('carouselTrack');

  protected readonly photos = signal<StampImageModel[]>([]);
  protected readonly isDragging = signal(false);
  protected readonly isLoading = signal(true);
  protected readonly isUploading = signal(false);
  protected readonly isDeleting = signal(false);
  protected readonly imageToDelete = signal<StampImageModel | null>(null);

  ngOnInit(): void {
    this.loadImages();
  }

  protected openFilePicker(): void {
    if (!this.isUploading()) {
      this.fileInput()?.nativeElement.click();
    }
  }

  protected onFileInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.addFiles(input.files);
    input.value = '';
  }

  protected onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(true);
  }

  protected onDragLeave(event: DragEvent): void {
    const current = event.currentTarget as HTMLElement;
    const next = event.relatedTarget as Node | null;
    if (!next || !current.contains(next)) {
      this.isDragging.set(false);
    }
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(false);
    this.addFiles(event.dataTransfer?.files ?? null);
  }

  protected scrollCarousel(direction: -1 | 1): void {
    this.carouselTrack()?.nativeElement.scrollBy({
      left: direction * 310,
      behavior: 'smooth'
    });
  }

  protected trackPhoto(_: number, photo: StampImageModel): number {
    return photo.id;
  }

  protected processImage(photo: StampImageModel): void {
    this.router.navigate(['/process', photo.id]);
  }

  protected requestDelete(photo: StampImageModel): void {
    this.imageToDelete.set(photo);
  }

  protected cancelDelete(): void {
    if (!this.isDeleting()) {
      this.imageToDelete.set(null);
    }
  }

  protected confirmDelete(): void {
    const photo = this.imageToDelete();
    if (!photo || this.isDeleting()) {
      return;
    }

    this.isDeleting.set(true);
    this.imageService.deleteImage(photo.id)
      .pipe(finalize(() => this.isDeleting.set(false)))
      .subscribe({
        next: () => {
          this.photos.update((photos) => photos.filter((item) => item.id !== photo.id));
          this.imageToDelete.set(null);
          this.toaster.success('Photo successfully deleted.');
        },
        error: () => {
          this.toaster.error('We could not delete that photo.');
        }
      });
  }

  private addFiles(files: FileList | null): void {
    if (!files || this.isUploading()) {
      return;
    }

    const images = Array.from(files).filter((file) => file.type.startsWith('image/'));
    if (!images.length) {
      this.toaster.info('Please choose one or more image files.');
      return;
    }

    this.isUploading.set(true);

    forkJoin(images.map((file) => this.imageService.uploadImage(file)))
      .pipe(finalize(() => this.isUploading.set(false)))
      .subscribe({
        next: (uploaded) => {
          this.photos.update((photos) => [...uploaded.reverse(), ...photos]);
          setTimeout(() => this.carouselTrack()?.nativeElement.scrollTo({
            left: 0,
            behavior: 'smooth'
          }));
          const label = uploaded.length === 1 ? 'Photo' : `${uploaded.length} photos`;
          this.toaster.success(`${label} successfully added.`);
        },
        error: () => {
          this.toaster.error('We could not upload those photos.');
        }
      });
  }

  private loadImages(): void {
    this.isLoading.set(true);

    this.imageService.getImages()
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (images) => {
          this.photos.set(images);
        },
        error: () => {
          this.toaster.error('We could not load your photos.');
        }
      });
  }
}
