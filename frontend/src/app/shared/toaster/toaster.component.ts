import {Component, inject} from '@angular/core';

import {ToasterService} from './toaster.service';

@Component({
  selector: 'app-toaster',
  templateUrl: './toaster.component.html',
  styleUrl: './toaster.component.scss'
})
export class ToasterComponent {
  protected readonly toaster = inject(ToasterService);
}
