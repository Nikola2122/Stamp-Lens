import {CommonModule} from '@angular/common';
import {Component, OnInit, inject, signal} from '@angular/core';
import {ActivatedRoute, RouterLink} from '@angular/router';
import {finalize} from 'rxjs';

import {StampImageModel} from '../models/StampImageModel';
import {StampImageService} from '../service/stamp-image.service';
import {ToasterComponent} from '../shared/toaster/toaster.component';
import {ToasterService} from '../shared/toaster/toaster.service';

@Component({
  selector: 'app-process-image',
  imports: [CommonModule, RouterLink, ToasterComponent],
  templateUrl: './process-image.component.html',
  styleUrl: './process-image.component.scss'
})
export class ProcessImageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly imageService = inject(StampImageService);
  private readonly toaster = inject(ToasterService);

  protected readonly image = signal<StampImageModel | null>(null);
  protected readonly isLoading = signal(true);

  ngOnInit(): void {
    const imageId = Number(this.route.snapshot.paramMap.get('id'));

    if (!Number.isInteger(imageId) || imageId <= 0) {
      this.isLoading.set(false);
      this.toaster.error('That image could not be found.');
      return;
    }

    this.imageService.getImage(imageId)
      .pipe(finalize(() => this.isLoading.set(false)))
      .subscribe({
        next: (image) => this.image.set(image),
        error: () => this.toaster.error('We could not load that image.')
      });
  }

  protected processImage(): void {
    this.toaster.info('Image processing will be connected in the next step.');
  }
}
