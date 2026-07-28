export interface StampImageData {
  id: number;
  original_name: string;
  file: string;
  extension: string;
  uploaded_at: string;
}

export class StampImageModel implements StampImageData {
  readonly id: number;
  readonly original_name: string;
  readonly file: string;
  readonly extension: string;
  readonly uploaded_at: string;

  constructor(data: StampImageData) {
    this.id = data.id;
    this.original_name = data.original_name;
    this.file = data.file;
    this.extension = data.extension;
    this.uploaded_at = data.uploaded_at;
  }

  get isNew(): boolean {
    const uploadedAt = new Date(this.uploaded_at).getTime();
    const halfAnHour = 30 * 60 * 1000;

    return Number.isFinite(uploadedAt)
      && Date.now() - uploadedAt >= 0
      && Date.now() - uploadedAt <= halfAnHour;
  }
}
