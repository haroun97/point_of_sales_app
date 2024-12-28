import { Component, OnInit } from '@angular/core';
import { EmployeeService } from '../services/employee/employee.service';
import { Option } from 'src/libs/matchy/src/models/classes/option';
import { ImportPossibleFields } from 'src/models/classes/interfaces/importPossibleField';
import { Matchy } from 'src/libs/matchy/src/main';
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
      
    })
  }
}