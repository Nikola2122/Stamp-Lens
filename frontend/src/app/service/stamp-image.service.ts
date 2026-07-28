import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import {map, Observable} from 'rxjs';
import {StampImageData, StampImageModel} from '../models/StampImageModel';
import {environment} from '../environment';

@Injectable({
  providedIn: 'root'
})
export class StampImageService {
  private readonly http = inject(HttpClient);
  private readonly url = environment.apiUrl;

  getImages(): Observable<StampImageModel[]> {
    return this.http.get<StampImageData[]>(`${this.url}/getAllImages/`)
      .pipe(map((images) => images.map((image) => new StampImageModel(image))));
  }

  getImage(imageId: number): Observable<StampImageModel> {
    return this.http.get<StampImageData>(`${this.url}/getImage/${imageId}/`)
      .pipe(map((image) => new StampImageModel(image)));
  }

  uploadImage(file: File): Observable<StampImageModel> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<StampImageData>(`${this.url}/uploadImage/`, formData)
      .pipe(map((image) => new StampImageModel(image)));
  }

  deleteImage(imageId: number): Observable<void> {
    return this.http.delete<void>(`${this.url}/deleteImage/${imageId}/`);
  }
}
