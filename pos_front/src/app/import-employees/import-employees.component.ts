import { Component, OnInit } from '@angular/core';
import { EmployeeService } from '../services/employee/employee.service';
import { Option } from 'src/libs/matchy/src/models/classes/option';
import { ImportPossibleFields } from 'src/models/interfaces/importPossibleField';
import { Matchy } from 'src/libs/matchy/src/main';
import { UploadEntry } from 'src/libs/matchy/src/models/classes/uploadEntry';
@Component({
  selector: 'app-import-employees',
  imports: [],
  templateUrl: './import-employees.component.html',
  styleUrl: './import-employees.component.css'
})

export class ImportEmployeesComponent implements OnInit {
  constructor(private employeeService: EmployeeService) {}

  ngOnInit(): void {
    this.loadMatchyLib();
  }
  loadMatchyLib(){ 
    this.employeeService.getOptions().subscribe((data: ImportPossibleFields) => {
      const matchy = new Matchy(data.possible_fields);
      document.getElementById("matchy")?.appendChild(matchy);

      matchy.submit = async(data: UploadEntry) => {
          const entry: MatchyUploadEntry = MatchyUploadEntry;
          en
          entry.focrceUpload = false;

          this.employeeService.upload(data).subscribe((data:BaseOut) => {
          return this.http.post.post<BaseOut>(endPointUrl, data)
        }
          
        )
      };

    })
  }
}
