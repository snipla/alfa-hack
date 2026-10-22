<?php

namespace App\Filament\Customer\Pages\Auth;

use Filament\Auth\Pages\Register as BaseRegister;
use Filament\Forms\Components\Checkbox;
use Filament\Forms\Components\TextInput;
use Filament\Schemas\Schema;

class Register extends BaseRegister
{
    public function form(Schema $schema): Schema
    {
        return parent::form($schema)
            ->components([
                $this->getNameFormComponent(),
                $this->getEmailFormComponent(),
//                TextInput::make('inn')
//                    ->label('ИНН')
//                    ->integer()
//                    ->required(),
                TextInput::make('target')
                    ->label('Цель кредитования')
                    ->maxLength(25)
                    ->required(),
                TextInput::make('borrower')
                    ->label('Заёмщик')
                    ->maxLength(25)
                    ->required(),
                $this->getPasswordFormComponent(),
                $this->getPasswordConfirmationFormComponent(),
                Checkbox::make('terms')
                    ->label('Я принимаю политику конфиденциальности и условия обработки данных')
                    ->required()
                    ->accepted()
                    ->dehydrated(false) // Не сохранять в БД
            ]);
    }
}
