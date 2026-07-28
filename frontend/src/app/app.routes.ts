import {Routes} from '@angular/router';

import {ProcessImageComponent} from './process-image/process-image.component';
import {StampWorkspaceComponent} from './stamp-workspace/stamp-workspace.component';

export const routes: Routes = [
  {
    path: '',
    component: StampWorkspaceComponent,
    title: 'Stamp Lens — Upload workspace'
  },
  {
    path: 'process/:id',
    component: ProcessImageComponent,
    title: 'Stamp Lens — Process image'
  },
  {path: '**', redirectTo: ''}
];
